"""SupabaseStore (P4): persistencia en Supabase con respaldo en memoria (RF-F0-06, anexo 90).

Cada escritura va primero a un `MemoryStore` interno y después a Supabase. Así «persistir antes de
emitir» (RT-05) se cumple aunque Supabase falle: si una llamada falla o supera `timeout_s`, el store
pasa a modo degradado (`degradado = True`, queda así), avisa en el log y el run continúa en memoria.
Mientras Supabase responde, las lecturas salen de Supabase, que es lo que permite consultar un run
tras reiniciar el backend.

Los objetos del contrato se guardan como `jsonb` (columna `data`); las demás columnas sirven para
consultar y ordenar. El esquema está en `supabase/migrations/0001_init.sql`. Solo el backend usa la
clave `service_role`.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Awaitable, Callable, TypeVar

from app.catalogo import cargar_catalogo_desde_dir
from app.contract import Catalogo, DecisionHumana, Evento, Plan, Run
from app.store.memory import MemoryStore

log = logging.getLogger("capataz.supabase")

T = TypeVar("T")

# Campo de `Catalogo` -> tabla (se llaman igual) y columnas relacionales extra de cada fila.
COLUMNAS_CATALOGO: dict[str, Callable[[dict], dict]] = {
    "peligros": lambda d: {},
    "tipos_tarea": lambda d: {},
    "controles": lambda d: {"peligro_id": d["peligro_id"], "bloqueante": d.get("bloqueante", True)},
    "personas": lambda d: {},
    "equipos": lambda d: {"tipo_equipo": d["tipo_equipo"]},
    "incidentes": lambda d: {"tipo_tarea": d.get("tipo_tarea"), "riesgo_critico": d.get("riesgo_critico")},
    "escenarios": lambda d: {},
}


def _json(modelo: Any) -> Any:
    """Objeto del contrato -> estructura JSON pura (fechas y enums como texto)."""
    return json.loads(modelo.model_dump_json())


def filas_catalogo(catalogo: Catalogo) -> dict[str, list[dict[str, Any]]]:
    """Filas por tabla del catálogo, listas para un upsert por `id` (lo usa scripts/cargar_seeds.py).

    `orden` guarda la posición en el archivo: al leer se conserva el orden del catálogo, que importa."""
    filas: dict[str, list[dict[str, Any]]] = {}
    for campo, extra in COLUMNAS_CATALOGO.items():
        filas[campo] = []
        for posicion, objeto in enumerate(getattr(catalogo, campo)):
            datos = _json(objeto)
            filas[campo].append({"id": datos["id"], "orden": posicion, **extra(datos), "data": datos})
    return filas


class SupabaseStore:
    nombre = "supabase"

    def __init__(
        self,
        url: str | None = None,
        clave: str | None = None,
        *,
        cliente: Any = None,
        data_dir: Path | None = None,
        dump_dir: Path | None = None,
        timeout_s: float | None = None,
    ) -> None:
        self._url, self._clave, self._cliente = url, clave, cliente
        self._timeout_s = timeout_s if timeout_s is not None else float(os.getenv("SUPABASE_TIMEOUT_S", "5"))
        self._data_dir = data_dir
        self._respaldo = MemoryStore(data_dir=data_dir, dump_dir=dump_dir)
        self._catalogo: Catalogo | None = None
        self.degradado = False

    @classmethod
    def desde_entorno(cls) -> "SupabaseStore":
        """Lee SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY. Sin ellas lanza error (el backend cae a memoria)."""
        from app.config import Settings

        url, clave = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not clave:
            raise RuntimeError("Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY")
        s = Settings()
        return cls(url, clave, data_dir=s.data_dir, dump_dir=s.memory_dump_dir)

    # -- acceso a Supabase ------------------------------------------------------------------

    async def _db(self) -> Any:
        if self._cliente is None:
            from supabase import acreate_client  # import diferido: el modo memory no lo necesita

            self._cliente = await acreate_client(self._url, self._clave)
        return self._cliente

    async def _intentar(self, operacion: Callable[[Any], Awaitable[T]]) -> tuple[bool, T | None]:
        """Ejecuta una operación en Supabase. (False, None) si ya está degradado o si falla ahora."""
        if self.degradado:
            return False, None
        try:
            db = await asyncio.wait_for(self._db(), self._timeout_s)
            return True, await asyncio.wait_for(operacion(db), self._timeout_s)
        except Exception as e:  # red, credenciales, tabla inexistente, tiempo límite...
            self.degradado = True
            log.error("Supabase no responde (%s: %s); el run continúa en memoria", type(e).__name__, e)
            return False, None

    # -- catálogo -----------------------------------------------------------------------------

    async def cargar_catalogo(self) -> Catalogo:
        if self._catalogo is not None:
            return self._catalogo

        async def leer(db: Any) -> dict[str, list]:
            datos = {}
            for campo in COLUMNAS_CATALOGO:
                filas = (await db.table(campo).select("data").order("orden").execute()).data
                datos[campo] = [f["data"] for f in filas]
            return datos

        ok, datos = await self._intentar(leer)
        if ok and any(datos.values()):
            self._catalogo = Catalogo.model_validate(datos)
        else:
            if ok:
                log.warning("Supabase no tiene seeds cargados (scripts/cargar_seeds.py): se usa data/*.json")
            self._catalogo = cargar_catalogo_desde_dir(self._data_dir)
        return self._catalogo

    # -- runs -----------------------------------------------------------------------------------

    @staticmethod
    def _fila_run(run: Run) -> dict[str, Any]:
        return {
            "id": run.id, "estado": run.estado.value, "modo": run.modo, "escenario_id": run.escenario_id,
            "tarea": _json(run.tarea), "data": _json(run),
            "creado_en": run.creado_en.isoformat(), "actualizado_en": run.actualizado_en.isoformat(),
        }

    async def crear_run(self, run: Run) -> None:
        await self._respaldo.crear_run(run)
        await self._intentar(lambda db: db.table("runs").upsert(self._fila_run(run), on_conflict="id").execute())

    async def actualizar_run(self, run: Run) -> None:
        await self._respaldo.actualizar_run(run)
        await self._intentar(lambda db: db.table("runs").upsert(self._fila_run(run), on_conflict="id").execute())

    async def leer_run(self, run_id: str) -> Run | None:
        ok, res = await self._intentar(lambda db: db.table("runs").select("data").eq("id", run_id).execute())
        if ok and res.data:
            return Run.model_validate(res.data[0]["data"])
        return await self._respaldo.leer_run(run_id)  # degradado, o creado mientras Supabase fallaba

    # -- eventos (auditoría) ----------------------------------------------------------------------

    async def agregar_evento(self, evento: Evento) -> None:
        await self._respaldo.agregar_evento(evento)
        fila = {"run_id": evento.run_id, "seq": evento.seq, "ts": evento.ts.isoformat(), "tipo": evento.tipo.value,
                "actor": evento.actor, "payload": _json(evento)["payload"]}
        # Idempotente por (run_id, seq): reintentar no duplica ni modifica (los eventos son inmutables).
        await self._intentar(lambda db: db.table("eventos").upsert(
            fila, on_conflict="run_id,seq", ignore_duplicates=True).execute())

    async def listar_eventos(self, run_id: str, desde_seq: int = 0) -> list[Evento]:
        ok, res = await self._intentar(lambda db: db.table("eventos").select("*").eq("run_id", run_id)
                                       .gt("seq", desde_seq).order("seq").execute())
        if ok:
            return [Evento.model_validate(f) for f in res.data]
        return await self._respaldo.listar_eventos(run_id, desde_seq)

    # -- plan y decisión ---------------------------------------------------------------------------

    async def guardar_plan(self, plan: Plan) -> None:
        await self._respaldo.guardar_plan(plan)
        fila = {"id": plan.id, "run_id": plan.run_id, "estado_sistema": plan.estado_sistema.value, "data": _json(plan)}
        await self._intentar(lambda db: db.table("planes").upsert(fila, on_conflict="id").execute())

    async def guardar_decision(self, run_id: str, decision: DecisionHumana) -> None:
        await self._respaldo.guardar_decision(run_id, decision)
        fila = {"run_id": run_id, "plan_id": decision.plan_id, "decision": decision.decision,
                "comentario": decision.comentario, "usuario": decision.usuario}
        await self._intentar(lambda db: db.table("decisiones").insert(fila).execute())
