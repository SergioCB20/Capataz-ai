"""Store sobre Supabase (API REST de PostgREST) con espejo en memoria.

Cada escritura va primero a memoria y luego a Supabase. Si Supabase falla o tarda,
se registra un aviso y el run continúa en memoria (anexo de Supabase, regla 7).
Las lecturas usan la memoria y, si el dato no está (p. ej. tras reiniciar), Supabase.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import httpx
from pydantic_core import to_jsonable_python

from app.catalogo import cargar_catalogo_desde_dir
from app.config import Settings  # carga el .env
from app.contract import Catalogo, DecisionHumana, Evento, Plan, Run
from app.store.memory import MemoryStore

log = logging.getLogger(__name__)

TABLAS_CATALOGO = ("peligros", "tipos_tarea", "controles", "personas", "equipos", "incidentes", "escenarios")


class SupabaseStore:
    nombre = "supabase"

    def __init__(self, url: str, clave: str, data_dir: Path | None = None, timeout_s: float = 5.0) -> None:
        self._base = url.rstrip("/") + "/rest/v1"
        self._headers = {"apikey": clave, "Content-Type": "application/json"}
        if clave.startswith("eyJ"):  # clave service_role en formato JWT (formato antiguo)
            self._headers["Authorization"] = f"Bearer {clave}"
        self._timeout = timeout_s
        self._data_dir = data_dir
        self._memoria = MemoryStore(data_dir=data_dir)
        self._catalogo: Catalogo | None = None

    @classmethod
    def desde_entorno(cls) -> "SupabaseStore":
        url = os.environ.get("SUPABASE_URL")
        clave = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not clave:
            raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")
        return cls(url, clave, data_dir=Settings().data_dir)

    # -- HTTP -------------------------------------------------------------------

    async def _pedir(self, metodo: str, tabla: str, *, params: dict | None = None,
                     cuerpo: Any = None, prefer: str | None = None) -> Any:
        headers = dict(self._headers)
        if prefer:
            headers["Prefer"] = prefer
        async with httpx.AsyncClient(timeout=self._timeout) as cliente:
            resp = await cliente.request(
                metodo, f"{self._base}/{tabla}", params=params, headers=headers,
                json=to_jsonable_python(cuerpo) if cuerpo is not None else None,
            )
        if resp.status_code >= 400:
            raise RuntimeError(f"Supabase {metodo} {tabla}: HTTP {resp.status_code} {resp.text[:200]}")
        return resp.json() if resp.content else None

    async def _intentar(self, descripcion: str, coro) -> None:
        """Escritura en Supabase que nunca tumba el run."""
        try:
            await coro
        except Exception as e:  # red, tiempo límite o error de PostgREST
            log.warning("No se pudo %s en Supabase; queda solo en memoria: %s", descripcion, e)

    async def upsert(self, tabla: str, filas: list[dict]) -> None:
        if filas:
            await self._pedir("POST", tabla, cuerpo=filas, prefer="resolution=merge-duplicates,return=minimal")

    # -- Catálogo -----------------------------------------------------------------

    async def cargar_catalogo(self) -> Catalogo:
        if self._catalogo is None:
            try:
                datos = {t: [f["data"] for f in await self._pedir("GET", t, params={"select": "data"})]
                         for t in TABLAS_CATALOGO}
            except Exception as e:
                log.warning("No se pudo leer el catálogo de Supabase; se usa data/: %s", e)
                datos = {}
            if any(datos.values()):
                self._catalogo = Catalogo.model_validate(datos)
            else:
                self._catalogo = cargar_catalogo_desde_dir(self._data_dir)
        return self._catalogo

    # -- Runs -------------------------------------------------------------------

    @staticmethod
    def _fila_run(run: Run) -> dict:
        return {
            "id": run.id, "estado": run.estado, "modo": run.modo, "escenario_id": run.escenario_id,
            "tarea": run.tarea, "data": run, "actualizado_en": run.actualizado_en,
        }

    async def crear_run(self, run: Run) -> None:
        await self._memoria.crear_run(run)
        await self._intentar("crear el run", self._pedir("POST", "runs", cuerpo=self._fila_run(run),
                                                         prefer="return=minimal"))

    async def leer_run(self, run_id: str) -> Run | None:
        run = await self._memoria.leer_run(run_id)
        if run is not None:
            return run
        try:
            filas = await self._pedir("GET", "runs", params={"select": "data", "id": f"eq.{run_id}"})
        except Exception as e:
            log.warning("No se pudo leer el run %s de Supabase: %s", run_id, e)
            return None
        if not filas:
            return None
        run = Run.model_validate(filas[0]["data"])
        await self._memoria.crear_run(run)
        for ev in await self._eventos_supabase(run_id, 0):
            await self._memoria.agregar_evento(ev)
        return run

    async def actualizar_run(self, run: Run) -> None:
        await self._memoria.actualizar_run(run)
        fila = self._fila_run(run)
        await self._intentar("actualizar el run", self._pedir(
            "PATCH", "runs", params={"id": f"eq.{run.id}"},
            cuerpo={k: fila[k] for k in ("estado", "data", "actualizado_en")}, prefer="return=minimal"))

    # -- Eventos ------------------------------------------------------------------

    async def agregar_evento(self, evento: Evento) -> None:
        await self._memoria.agregar_evento(evento)
        await self._intentar("guardar el evento", self._pedir(
            "POST", "eventos", cuerpo=evento.model_dump(mode="json"),
            prefer="resolution=ignore-duplicates,return=minimal"))

    async def _eventos_supabase(self, run_id: str, desde_seq: int) -> list[Evento]:
        filas = await self._pedir("GET", "eventos", params={
            "select": "run_id,seq,ts,tipo,actor,payload", "run_id": f"eq.{run_id}",
            "seq": f"gt.{desde_seq}", "order": "seq.asc"})
        return [Evento.model_validate(f) for f in filas]

    async def listar_eventos(self, run_id: str, desde_seq: int = 0) -> list[Evento]:
        eventos = await self._memoria.listar_eventos(run_id, desde_seq)
        if eventos or await self._memoria.leer_run(run_id) is not None:
            return eventos
        try:
            return await self._eventos_supabase(run_id, desde_seq)
        except Exception as e:
            log.warning("No se pudieron leer eventos de Supabase: %s", e)
            return []

    # -- Plan y decisión ------------------------------------------------------------

    async def guardar_plan(self, plan: Plan) -> None:
        await self._memoria.guardar_plan(plan)
        await self._intentar("guardar el plan", self.upsert("planes", [
            {"id": plan.id, "run_id": plan.run_id, "estado_sistema": plan.estado_sistema, "data": plan}]))

    async def guardar_decision(self, run_id: str, decision: DecisionHumana) -> None:
        await self._memoria.guardar_decision(run_id, decision)
        await self._intentar("guardar la decisión", self._pedir("POST", "decisiones", cuerpo={
            "run_id": run_id, "plan_id": decision.plan_id, "decision": decision.decision,
            "comentario": decision.comentario, "usuario": decision.usuario}, prefer="return=minimal"))
