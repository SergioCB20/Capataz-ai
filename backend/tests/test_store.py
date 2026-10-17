"""Suite de Store: la misma para MemoryStore y SupabaseStore (RF-F0-06).

P4: para correrla contra Supabase, añade una fábrica a `FABRICAS` (p. ej. cuando
`STORE_TEST_SUPABASE=1`) que devuelva un `SupabaseStore` limpio.
"""

import os
from datetime import date

import pytest

from app.contract import (
    DecisionHumana,
    EstadoRun,
    EstadoSistema,
    Evento,
    Plan,
    Run,
    Tarea,
    TipoEvento,
    TurnoRef,
)
from app.store import MemoryStore


def _memory(tmp_path):
    return MemoryStore(data_dir=None, dump_dir=tmp_path)


FABRICAS = {"memory": _memory}

if os.getenv("STORE_TEST_SUPABASE") == "1":
    from app.store.supabase_store import SupabaseStore  # P4

    FABRICAS["supabase"] = lambda _tmp: SupabaseStore.desde_entorno()


@pytest.fixture(params=list(FABRICAS))
def store(request, tmp_path):
    return FABRICAS[request.param](tmp_path)


def _run() -> Run:
    return Run(tarea=Tarea(tipo_tarea="TT", turno=TurnoRef(fecha=date(2026, 10, 17), turno="dia")))


def _evento(run_id: str, seq: int) -> Evento:
    return Evento(run_id=run_id, seq=seq, tipo=TipoEvento.RUN_ERROR, actor="sistema", payload={"mensaje": "x"})


async def test_crear_leer_actualizar_run(store):
    run = _run()
    await store.crear_run(run)
    leido = await store.leer_run(run.id)
    assert leido.id == run.id and leido.estado == EstadoRun.EVALUANDO
    leido.estado = EstadoRun.ESPERANDO_DECISION
    await store.actualizar_run(leido)
    assert (await store.leer_run(run.id)).estado == EstadoRun.ESPERANDO_DECISION
    assert await store.leer_run("no-existe") is None


async def test_eventos_idempotentes_y_ordenados(store):
    run = _run()
    await store.crear_run(run)
    for seq in (2, 1, 3, 2):
        await store.agregar_evento(_evento(run.id, seq))
    assert [e.seq for e in await store.listar_eventos(run.id)] == [1, 2, 3]
    assert [e.seq for e in await store.listar_eventos(run.id, desde_seq=1)] == [2, 3]


async def test_plan_y_decision(store):
    run = _run()
    await store.crear_run(run)
    plan = Plan(run_id=run.id, estado_sistema=EstadoSistema.RECOMENDADO)
    await store.guardar_plan(plan)
    await store.guardar_decision(run.id, DecisionHumana(plan_id=plan.id, decision="aprobar"))


async def test_catalogo_de_juguete_sin_data(store):
    catalogo = await store.cargar_catalogo()
    assert catalogo.escenario("E1") is not None
