import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.config import Settings
from app.contract import EstadoRun, TipoEvento, validar_payload, Evento
from app.main import create_app
from app.store import MemoryStore


@pytest.fixture
def settings(tmp_path):
    s = Settings()
    s.data_dir = tmp_path / "data_vacia"  # sin archivos ⇒ seed de juguete
    s.replays_dir = tmp_path / "replays"
    s.memory_dump_dir = tmp_path / "memoria"
    s.replay_velocidad = 100.0
    s.replay_max_espera_s = 0.01
    s.store_backend = "memory"
    return s


@pytest.fixture
async def client(settings):
    app = create_app(settings, MemoryStore(data_dir=settings.data_dir, dump_dir=settings.memory_dump_dir))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        c.app = app
        yield c


async def _esperar_estado(client, run_id, estado, intentos=200):
    for _ in range(intentos):
        run = (await client.get(f"/api/runs/{run_id}")).json()
        if run["estado"] == estado:
            return run
        await asyncio.sleep(0.01)
    raise AssertionError(f"El run no llegó a {estado}; quedó en {run['estado']}")


async def _run_hasta_decision(client):
    run_id = (await client.post("/api/runs", json={"escenario_id": "E1"})).json()["run_id"]
    run = await _esperar_estado(client, run_id, "ESPERANDO_CAMPO")
    resp = await client.post(
        f"/api/runs/{run_id}/campo",
        json={"usuario": "ana", "respuestas": [
            {"requisito_id": r, "cumple": True, "nota": "ok"} for r in ("REQ-JUG-01", "REQ-JUG-02", "REQ-JUG-03")
        ]},
    )
    assert resp.status_code == 200
    return run_id, await _esperar_estado(client, run_id, "ESPERANDO_DECISION")


async def test_health_y_catalogo(client):
    health = (await client.get("/api/health")).json()
    assert health["store"] == "memory" and health["orquestador"] in ("stub", "p2")
    assert (await client.get("/api/catalogo")).json()["escenarios"][0]["id"] == "E1"


async def test_flujo_completo_e1_y_eventos_validos(client):
    run_id, run = await _run_hasta_decision(client)
    resp = await client.post(f"/api/runs/{run_id}/decision", json={"plan_id": run["plan"]["id"], "decision": "aprobar"})
    assert resp.status_code == 200 and resp.json()["estado"] == "APROBADA"

    eventos = [Evento.model_validate(e) for e in (await client.get(f"/api/runs/{run_id}/auditoria")).json()]
    assert [e.seq for e in eventos] == list(range(1, len(eventos) + 1))  # sin huecos
    for e in eventos:
        validar_payload(e)
    assert eventos[0].tipo == TipoEvento.RUN_INICIADO
    assert eventos[-1].tipo == TipoEvento.RUN_FINALIZADO

    # decisión duplicada ⇒ 409
    dup = await client.post(f"/api/runs/{run_id}/decision", json={"plan_id": run["plan"]["id"], "decision": "aprobar"})
    assert dup.status_code == 409
    # un run terminal no acepta confirmaciones
    assert (await client.post(f"/api/runs/{run_id}/campo", json={"respuestas": []})).status_code == 409


async def test_rechazo_sin_comentario_422(client):
    run_id, run = await _run_hasta_decision(client)
    resp = await client.post(f"/api/runs/{run_id}/decision", json={"plan_id": run["plan"]["id"], "decision": "rechazar"})
    assert resp.status_code == 422


async def test_aprobar_plan_bloqueado_409(client):
    run_id = (await client.post("/api/runs", json={"escenario_id": "E1"})).json()["run_id"]
    await _esperar_estado(client, run_id, "ESPERANDO_CAMPO")
    await client.post(
        f"/api/runs/{run_id}/campo",
        json={"respuestas": [{"requisito_id": "REQ-JUG-02", "cumple": False, "nota": "en mantenimiento"}]},
    )
    run = await _esperar_estado(client, run_id, "ESPERANDO_DECISION")
    assert run["plan"]["estado_sistema"] == "BLOQUEADO"
    plan_id = run["plan"]["id"]
    assert (await client.post(f"/api/runs/{run_id}/decision", json={"plan_id": plan_id, "decision": "aprobar"})).status_code == 409
    assert (await client.get(f"/api/runs/{run_id}")).json()["estado"] == "ESPERANDO_DECISION"
    resp = await client.post(
        f"/api/runs/{run_id}/decision", json={"plan_id": plan_id, "decision": "rechazar", "comentario": "sin equipo"}
    )
    assert resp.json()["estado"] == "BLOQUEADA"


async def test_sse_reenvia_desde_last_event_id(client):
    run_id, run = await _run_hasta_decision(client)
    await client.post(f"/api/runs/{run_id}/decision", json={"plan_id": run["plan"]["id"], "decision": "aprobar"})
    total = len((await client.get(f"/api/runs/{run_id}/auditoria")).json())

    async with client.stream("GET", f"/api/runs/{run_id}/eventos", headers={"Last-Event-ID": "3"}) as resp:
        datos = [json.loads(l[5:]) async for l in resp.aiter_lines() if l.startswith("data:")]
    assert [d["seq"] for d in datos] == list(range(4, total + 1))


async def test_run_inexistente_404(client):
    assert (await client.get("/api/runs/no-existe")).status_code == 404


async def test_replay_reproduce_y_acepta_decision(client, settings):
    # Grabar un run real y reproducirlo como replay de E1.
    run_id, run = await _run_hasta_decision(client)
    await client.post(f"/api/runs/{run_id}/decision", json={"plan_id": run["plan"]["id"], "decision": "aprobar"})
    eventos = (await client.get(f"/api/runs/{run_id}/auditoria")).json()
    settings.replays_dir.mkdir(parents=True)
    (settings.replays_dir / "E1.json").write_text(json.dumps(eventos), encoding="utf-8")

    rid = (await client.post("/api/runs", json={"modo": "replay", "escenario_id": "E1"})).json()["run_id"]
    await _esperar_estado(client, rid, "ESPERANDO_CAMPO")
    await client.post(f"/api/runs/{rid}/campo", json={"respuestas": [{"requisito_id": "REQ-JUG-03", "cumple": True}]})
    rep = await _esperar_estado(client, rid, "ESPERANDO_DECISION")
    resp = await client.post(f"/api/runs/{rid}/decision", json={"plan_id": rep["plan"]["id"], "decision": "aprobar"})
    assert resp.json()["estado"] == "APROBADA"
    assert (await client.get(f"/api/runs/{rid}")).json()["modo"] == "replay"


async def test_replay_inexistente_404(client):
    assert (await client.post("/api/runs", json={"modo": "replay", "escenario_id": "E9"})).status_code == 404


async def test_fallo_del_orquestador_termina_en_error(client, monkeypatch):
    import app.runtime as runtime

    async def explota(run, catalogo, emitir):
        raise RuntimeError("agente caído")

    monkeypatch.setattr(runtime, "obtener_orquestador", lambda: (explota, None, "test"))
    run_id = (await client.post("/api/runs", json={"escenario_id": "E1"})).json()["run_id"]
    await _esperar_estado(client, run_id, "ERROR")
