"""API FastAPI de CAPATAZ. Arranque: `uv run uvicorn app.main:app --reload` (desde backend/)."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from app.config import Settings
from app.contract import (
    ESTADOS_TERMINALES,
    Catalogo,
    ConfirmacionesCampo,
    DecisionHumana,
    Evento,
    Run,
    RunCrear,
    RunCreado,
)
from app.orquestador import obtener_orquestador
from app.runtime import EVENTOS_FINALES, ErrorDeRun, RunManager
from app.store import MemoryStore, Store

log = logging.getLogger(__name__)


def crear_store(settings: Settings) -> Store:
    if settings.store_backend == "supabase":
        try:
            from app.store.supabase_store import SupabaseStore  # P4

            return SupabaseStore.desde_entorno()
        except Exception:
            log.exception("No se pudo iniciar SupabaseStore; se usa MemoryStore")
    return MemoryStore(data_dir=settings.data_dir, dump_dir=settings.memory_dump_dir)


def create_app(settings: Settings | None = None, store: Store | None = None) -> FastAPI:
    settings = settings or Settings()
    manager = RunManager(settings, store or crear_store(settings))

    app = FastAPI(title="CAPATAZ API", version="0.1.0")
    app.state.manager = manager
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ErrorDeRun)
    async def _error_de_run(_: Request, e: ErrorDeRun) -> JSONResponse:
        return JSONResponse(status_code=e.status, content={"detail": e.mensaje})

    @app.get("/api/health")
    async def health() -> dict:
        _, _, origen = obtener_orquestador()
        return {"store": manager.store.nombre, "llm_mode": settings.llm_mode, "orquestador": origen}

    @app.get("/api/catalogo", response_model=Catalogo)
    async def catalogo() -> Catalogo:
        return await manager.catalogo()

    @app.post("/api/runs", response_model=RunCreado)
    async def crear_run(datos: RunCrear) -> RunCreado:
        run = await manager.crear_run(datos)
        return RunCreado(run_id=run.id)

    @app.get("/api/runs/{run_id}", response_model=Run)
    async def leer_run(run_id: str) -> Run:
        return await manager.leer_run(run_id)

    @app.get("/api/runs/{run_id}/auditoria", response_model=list[Evento])
    async def auditoria(run_id: str) -> list[Evento]:
        """Todos los eventos del run en orden (exportar auditoría, grabar replays)."""
        return await manager.listar_eventos(run_id)

    @app.get("/api/runs/{run_id}/eventos")
    async def eventos(run_id: str, request: Request, desde: int = 0) -> EventSourceResponse:
        await manager.leer_run(run_id)  # 404 si no existe
        ultimo = request.headers.get("last-event-id")
        desde_seq = int(ultimo) if ultimo and ultimo.isdigit() else desde

        async def flujo():
            cola = manager.suscribir(run_id)
            try:
                visto = desde_seq
                for ev in await manager.listar_eventos(run_id, desde_seq):
                    yield {"id": str(ev.seq), "data": ev.model_dump_json()}
                    visto = ev.seq
                    if ev.tipo in EVENTOS_FINALES:
                        return
                if (await manager.leer_run(run_id)).estado in ESTADOS_TERMINALES:
                    return
                # Queda abierto (con latidos) hasta run.finalizado o run.error.
                while True:
                    ev = await cola.get()
                    if ev.seq <= visto:
                        continue
                    yield {"id": str(ev.seq), "data": ev.model_dump_json()}
                    visto = ev.seq
                    if ev.tipo in EVENTOS_FINALES:
                        return
            finally:
                manager.desuscribir(run_id, cola)

        return EventSourceResponse(flujo(), ping=15)

    @app.post("/api/runs/{run_id}/decision", response_model=Run)
    async def decision(run_id: str, datos: DecisionHumana) -> Run:
        return await manager.decidir(run_id, datos)

    @app.post("/api/runs/{run_id}/campo", response_model=Run)
    async def campo(run_id: str, datos: ConfirmacionesCampo) -> Run:
        return await manager.confirmar_campo(run_id, datos)

    return app


app = create_app()
