"""Ejecución de runs: emitir eventos, transiciones de estado, decisiones y campo."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel
from pydantic_core import to_jsonable_python

from app.config import Settings
from app.contract import (
    ACTOR_SISTEMA,
    ESTADOS_TERMINALES,
    Catalogo,
    ConfirmacionesCampo,
    DecisionHumana,
    Emitir,
    EstadoRun,
    EstadoSistema,
    Evento,
    Plan,
    PayloadDecisionTomada,
    PayloadPlanListo,
    PayloadRunFinalizado,
    Run,
    RunCrear,
    TipoEvento,
    actor_humano,
    validar_payload,
)
from app.orquestador import obtener_orquestador
from app.replay import ReplayPlayer, cargar_replay
from app.store import MemoryStore, Store

log = logging.getLogger(__name__)

EVENTOS_FINALES = frozenset({TipoEvento.RUN_FINALIZADO, TipoEvento.RUN_ERROR})


class ErrorDeRun(Exception):
    """Error de negocio que la API traduce a un código HTTP."""

    def __init__(self, status: int, mensaje: str) -> None:
        super().__init__(mensaje)
        self.status = status
        self.mensaje = mensaje


class RunManager:
    def __init__(self, settings: Settings, store: Store) -> None:
        self.settings = settings
        self.store = store
        # Replay nunca persiste en Supabase (RF-F3-05).
        self.store_replay = MemoryStore(data_dir=settings.data_dir)
        self._modo: dict[str, str] = {}
        self._seq: dict[str, int] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._locks_humano: dict[str, asyncio.Lock] = {}
        self._subs: dict[str, set[asyncio.Queue[Evento]]] = {}
        self._replays: dict[str, ReplayPlayer] = {}
        self._tareas: set[asyncio.Task] = set()

    # -- utilidades -----------------------------------------------------------

    def _store_de(self, run_id: str) -> Store:
        return self.store_replay if self._modo.get(run_id) == "replay" else self.store

    async def catalogo(self) -> Catalogo:
        return await self.store.cargar_catalogo()

    async def leer_run(self, run_id: str) -> Run:
        run = await self._store_de(run_id).leer_run(run_id)
        if run is None:
            raise ErrorDeRun(404, f"Run {run_id} no existe")
        return run

    async def listar_eventos(self, run_id: str, desde_seq: int = 0) -> list[Evento]:
        await self.leer_run(run_id)
        return await self._store_de(run_id).listar_eventos(run_id, desde_seq)

    def _lanzar(self, coro) -> None:
        tarea = asyncio.create_task(coro)
        self._tareas.add(tarea)
        tarea.add_done_callback(self._tareas.discard)

    # -- suscripciones (SSE) --------------------------------------------------

    def suscribir(self, run_id: str) -> asyncio.Queue[Evento]:
        cola: asyncio.Queue[Evento] = asyncio.Queue()
        self._subs.setdefault(run_id, set()).add(cola)
        return cola

    def desuscribir(self, run_id: str, cola: asyncio.Queue[Evento]) -> None:
        self._subs.get(run_id, set()).discard(cola)

    # -- emitir ---------------------------------------------------------------

    def emisor(self, run_id: str) -> Emitir:
        async def emitir(tipo: TipoEvento, actor: str, payload: dict[str, Any] | BaseModel) -> Evento:
            return await self._emitir(run_id, TipoEvento(tipo), actor, payload)

        return emitir

    async def _emitir(
        self, run_id: str, tipo: TipoEvento, actor: str, payload: dict[str, Any] | BaseModel
    ) -> Evento:
        store = self._store_de(run_id)
        async with self._locks.setdefault(run_id, asyncio.Lock()):
            seq = self._seq.get(run_id, 0) + 1
            evento = Evento(
                run_id=run_id,
                seq=seq,
                tipo=tipo,
                actor=actor,
                payload=to_jsonable_python(payload),
            )
            validar_payload(evento)  # un payload inválido es un bug: que se vea
            await store.agregar_evento(evento)  # persistir antes de emitir (RT-05)
            self._seq[run_id] = seq
            await self._aplicar(store, evento)
        for cola in list(self._subs.get(run_id, ())):
            cola.put_nowait(evento)
        return evento

    async def _aplicar(self, store: Store, ev: Evento) -> None:
        """Actualiza el Run según el evento (máquina de estados de EstadoRun)."""
        run = await store.leer_run(ev.run_id)
        if run is None:
            return
        t = ev.tipo
        if t == TipoEvento.RUN_INICIADO:
            run.estado = EstadoRun.EVALUANDO
        elif t == TipoEvento.CONFLICTO_DETECTADO:
            run.estado = EstadoRun.RESOLVIENDO_CONFLICTO
        elif t == TipoEvento.PLAN_LISTO:
            p = PayloadPlanListo.model_validate(ev.payload)
            run.plan, run.planes_alternativos = p.plan, p.planes_alternativos
            for plan in [p.plan, *p.planes_alternativos]:
                await store.guardar_plan(plan)
        elif t == TipoEvento.HUMANO_CAMPO_REQUERIDO:
            run.estado = EstadoRun.ESPERANDO_CAMPO
        elif t == TipoEvento.HUMANO_CAMPO_CONFIRMADO:
            run.estado = EstadoRun.EVALUANDO
        elif t == TipoEvento.HUMANO_DECISION_REQUERIDA:
            run.estado = EstadoRun.ESPERANDO_DECISION
        elif t == TipoEvento.HUMANO_DECISION_TOMADA:
            run.decision = PayloadDecisionTomada.model_validate(ev.payload).decision
            await store.guardar_decision(run.id, run.decision)
        elif t == TipoEvento.RUN_FINALIZADO:
            run.estado = PayloadRunFinalizado.model_validate(ev.payload).estado
        elif t == TipoEvento.RUN_ERROR:
            run.estado = EstadoRun.ERROR
        run.actualizado_en = datetime.now(timezone.utc)
        await store.actualizar_run(run)

    # -- crear y ejecutar -----------------------------------------------------

    async def crear_run(self, datos: RunCrear) -> Run:
        if datos.modo == "replay":
            # Sin red (RT-08): el replay nunca toca Supabase, ni para el catálogo.
            return await self._crear_replay(datos, await self.store_replay.cargar_catalogo())
        catalogo = await self.catalogo()

        tarea = datos.tarea
        if tarea is None:
            escenario = catalogo.escenario(datos.escenario_id or "")
            if escenario is None:
                raise ErrorDeRun(404, f"Escenario {datos.escenario_id} no existe")
            tarea = escenario.tarea
        run = Run(modo="vivo", escenario_id=datos.escenario_id, tarea=tarea)
        self._modo[run.id] = "vivo"
        await self.store.crear_run(run)
        self._lanzar(self._ejecutar(run, catalogo))
        return run

    async def _ejecutar(self, run: Run, catalogo: Catalogo) -> None:
        ejecutar_run, _, _ = obtener_orquestador()
        try:
            await asyncio.wait_for(
                ejecutar_run(run, catalogo, self.emisor(run.id)), timeout=self.settings.run_timeout_s
            )
        except Exception as e:  # RF-F1-06: el run nunca queda colgado
            log.exception("Fallo en el run %s", run.id)
            await self._error(run.id, e)

    async def _error(self, run_id: str, e: BaseException) -> None:
        run = await self._store_de(run_id).leer_run(run_id)
        if run and run.estado not in ESTADOS_TERMINALES:
            mensaje = "Tiempo límite del run agotado" if isinstance(e, TimeoutError) else f"{type(e).__name__}: {e}"
            await self._emitir(run_id, TipoEvento.RUN_ERROR, ACTOR_SISTEMA, {"mensaje": mensaje})

    async def _crear_replay(self, datos: RunCrear, catalogo: Catalogo) -> Run:
        eventos = cargar_replay(self.settings.replays_dir, datos.escenario_id or "")
        if eventos is None:
            raise ErrorDeRun(404, f"No hay replay para {datos.escenario_id}")
        escenario = catalogo.escenario(datos.escenario_id or "")
        tarea = ReplayPlayer.tarea_de(eventos) or (escenario.tarea if escenario else None)
        if tarea is None:
            raise ErrorDeRun(422, f"El replay {datos.escenario_id} no trae la tarea")
        run = Run(modo="replay", escenario_id=datos.escenario_id, tarea=tarea)
        self._modo[run.id] = "replay"
        await self.store_replay.crear_run(run)
        player = ReplayPlayer(
            eventos,
            self.emisor(run.id),
            velocidad=self.settings.replay_velocidad,
            max_espera_s=self.settings.replay_max_espera_s,
        )
        self._replays[run.id] = player
        self._lanzar(self._reproducir(run.id, player))
        return run

    async def _reproducir(self, run_id: str, player: ReplayPlayer) -> None:
        try:
            await player.reproducir()
        except Exception as e:
            log.exception("Fallo en el replay %s", run_id)
            await self._error(run_id, e)

    # -- personas ---------------------------------------------------------------

    async def decidir(self, run_id: str, decision: DecisionHumana) -> Run:
        async with self._locks_humano.setdefault(run_id, asyncio.Lock()):
            run = await self.leer_run(run_id)
            if run.estado != EstadoRun.ESPERANDO_DECISION:
                raise ErrorDeRun(409, f"El run no espera una decisión (estado {run.estado})")
            candidatos: list[Plan] = [p for p in [run.plan, *run.planes_alternativos] if p]
            plan = next((p for p in candidatos if p.id == decision.plan_id), None)
            if plan is None:
                raise ErrorDeRun(422, f"plan_id {decision.plan_id} no pertenece a este run")
            if decision.decision == "aprobar" and plan.estado_sistema != EstadoSistema.RECOMENDADO:
                raise ErrorDeRun(409, f"Un plan {plan.estado_sistema} no se puede aprobar; solo rechazar")

            if plan.id != (run.plan.id if run.plan else None):
                run.plan = plan  # el humano eligió una alternativa (RF-F2-21)
                await self._store_de(run_id).actualizar_run(run)

            emitir = self.emisor(run_id)
            await emitir(TipoEvento.HUMANO_DECISION_TOMADA, actor_humano(decision.usuario), {"decision": decision})
            if decision.decision == "aprobar":
                final = EstadoRun.APROBADA
            elif plan.estado_sistema == EstadoSistema.BLOQUEADO:
                final = EstadoRun.BLOQUEADA
            else:
                final = EstadoRun.RECHAZADA
            await emitir(TipoEvento.RUN_FINALIZADO, ACTOR_SISTEMA, {"estado": final})
            return await self.leer_run(run_id)

    async def confirmar_campo(self, run_id: str, conf: ConfirmacionesCampo) -> Run:
        async with self._locks_humano.setdefault(run_id, asyncio.Lock()):
            run = await self.leer_run(run_id)
            if run.estado != EstadoRun.ESPERANDO_CAMPO:
                raise ErrorDeRun(409, f"El run no espera confirmación de campo (estado {run.estado})")
            await self.emisor(run_id)(
                TipoEvento.HUMANO_CAMPO_CONFIRMADO, actor_humano(conf.usuario), {"confirmaciones": conf}
            )
            if run_id in self._replays:
                self._lanzar(self._reproducir(run_id, self._replays[run_id]))
            else:
                self._lanzar(self._confirmar(run, conf))
            return await self.leer_run(run_id)

    async def _confirmar(self, run: Run, conf: ConfirmacionesCampo) -> None:
        _, confirmar_campo, _ = obtener_orquestador()
        try:
            await asyncio.wait_for(
                confirmar_campo(run, await self.catalogo(), conf, self.emisor(run.id)),
                timeout=self.settings.run_timeout_s,
            )
        except Exception as e:
            log.exception("Fallo al confirmar campo en %s", run.id)
            await self._error(run.id, e)
