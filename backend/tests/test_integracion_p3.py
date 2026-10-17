"""P2 + P3 juntos: el Supervisor con los agentes y herramientas reales (sin verificadores de prueba)."""
import asyncio

import httpx
import pytest
from p3_datos import catalogo_p3, tarea
from pydantic_core import to_jsonable_python

from app.agents import _p3
from app.agents.supervisor import Dependencias, ejecutar_run
from app.config import Settings
from app.contract import EstadoSistema, Evento, Run, TipoEvento, validar_payload
from app.llm import ClienteLLM, set_cliente
from app.main import create_app
from app.store import MemoryStore


class Emisor:
    def __init__(self):
        self.eventos: list[Evento] = []

    async def __call__(self, tipo, actor, payload):
        ev = Evento(run_id="r", seq=len(self.eventos) + 1, tipo=tipo, actor=actor, payload=to_jsonable_python(payload))
        validar_payload(ev)
        self.eventos.append(ev)
        return ev

    def de_tipo(self, tipo):
        return [e for e in self.eventos if e.tipo == tipo]


def correr(cat, tarea_):
    emisor = Emisor()
    deps = Dependencias(verificar_personal=_p3.verificar_personal, verificar_equipo=_p3.verificar_equipo,
                        buscar=_p3.buscar_incidentes, cliente=ClienteLLM(modo="fake"))
    plan = asyncio.run(ejecutar_run(Run(id="r", tarea=tarea_), cat, emisor, deps=deps))
    return plan, emisor


def test_p2_usa_los_modulos_reales_de_p3():
    assert _p3.ORIGEN == {"verificar_personal": "p3", "verificar_equipo": "p3", "buscar_incidentes": "p3"}


def test_caso_limpio_se_recomienda_con_trazas_de_herramientas():
    plan, emisor = correr(catalogo_p3(), tarea(["PER-1"], ["EQ-1"]))
    assert plan.estado_sistema == EstadoSistema.RECOMENDADO and plan.cambios == []
    herramientas = {e.payload["trace"]["nombre"] for e in emisor.de_tipo(TipoEvento.AGENTE_HERRAMIENTA)}
    assert {"buscar_incidentes", "verificar_certificacion", "consultar_estado_equipo"} <= herramientas
    assert emisor.eventos[-1].tipo == TipoEvento.HUMANO_DECISION_REQUERIDA


def test_conflicto_se_resuelve_con_una_alternativa_verificada_por_las_herramientas_reales():
    # PER-2 tiene la certificación vencida y EQ-2 está en mantenimiento.
    plan, emisor = correr(catalogo_p3(), tarea(["PER-2"], ["EQ-2"]))
    causas = [e.payload["causa"] for e in emisor.de_tipo(TipoEvento.CONFLICTO_DETECTADO)]
    assert any("venció" in c for c in causas) and any("mantenimiento" in c for c in causas)

    # Alternativa 1: PER-5 es la de certificación más reciente, pero está ocupada por TA-OCUPA ⇒ la rechazan las herramientas.
    verificadas = [e.payload["alternativa"] for e in emisor.de_tipo(TipoEvento.CONFLICTO_ALTERNATIVA_VERIFICADA)]
    assert verificadas[0]["cumple_bloqueantes"] is False and "ya está asignada" in verificadas[0]["motivo_fallo"]
    # Alternativa 2: EQ-3 (perforadora equivalente, solo válida en alternativas) + PER-3 (SOST-B equivalente).
    assert verificadas[1]["cumple_bloqueantes"] is True
    assert plan.estado_sistema == EstadoSistema.RECOMENDADO
    assert plan.asignacion.equipos == ["EQ-3"] and plan.asignacion.personas == ["PER-3"]
    listo = emisor.de_tipo(TipoEvento.PLAN_LISTO)[0].payload
    assert listo["plan"]["estado_sistema"] == "BLOQUEADO" and listo["planes_alternativos"][0]["id"] == plan.id


def test_sin_alternativa_segura_queda_bloqueado():
    cat = catalogo_p3()
    cat.personas = [p for p in cat.personas if p.id in ("PER-2", "PER-4", "PER-5")]   # nadie libre y certificado
    cat.equipos = [e for e in cat.equipos if e.id in ("EQ-2", "EQ-4")]                # sin empernador utilizable
    plan, emisor = correr(cat, tarea(["PER-2"], ["EQ-2"]))
    assert plan.estado_sistema == EstadoSistema.BLOQUEADO and plan.escalamiento
    assert [e.payload["ronda"] for e in emisor.de_tipo(TipoEvento.CONFLICTO_ALTERNATIVAS)] == [1, 2]
    assert emisor.eventos[-1].payload == {"plan_id": plan.id, "solo_rechazo": True}


def test_el_patron_de_incidentes_suma_un_control_que_la_lista_base_no_tenia():
    _, emisor = correr(catalogo_p3(), tarea(["PER-4"], ["EQ-4"], tipo="TT-ALT"))  # PER-4 no tiene ARNES
    primera_pasada = emisor.de_tipo(TipoEvento.SUPERVISOR_CONSOLIDADO)[0].payload
    estados = {rc["control_id"]: rc["estado"] for rc in primera_pasada["resultados"]}
    assert estados == {"CTL-PLAT": "CUMPLE", "CTL-ARNES": "NO_CUMPLE"}  # CTL-ARNES solo llega por el incidente INC-3
    assert primera_pasada["estado_sistema"] == "BLOQUEADO"


@pytest.fixture
async def client(tmp_path):
    s = Settings()
    s.data_dir, s.replays_dir, s.memory_dump_dir = tmp_path / "vacio", tmp_path / "replays", tmp_path / "memoria"
    s.store_backend = "memory"
    set_cliente(ClienteLLM(modo="fake"))
    app = create_app(s, MemoryStore(data_dir=s.data_dir, dump_dir=s.memory_dump_dir))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c
    set_cliente(None)


async def _estado(client, run_id, estado):
    for _ in range(300):
        run = (await client.get(f"/api/runs/{run_id}")).json()
        if run["estado"] == estado:
            return run
        await asyncio.sleep(0.01)
    raise AssertionError(f"El run quedó en {run['estado']}, no en {estado}")


async def test_api_e1_de_punta_a_punta_con_p2_y_p3_reales_y_el_catalogo_de_juguete(client):
    assert (await client.get("/api/health")).json()["orquestador"] == "p2"
    run_id = (await client.post("/api/runs", json={"escenario_id": "E1"})).json()["run_id"]
    await _estado(client, run_id, "ESPERANDO_CAMPO")   # solo queda pendiente la condición de campo
    await client.post(f"/api/runs/{run_id}/campo",
                      json={"usuario": "ana", "respuestas": [{"requisito_id": "REQ-JUG-03", "cumple": True}]})
    run = await _estado(client, run_id, "ESPERANDO_DECISION")
    assert run["plan"]["estado_sistema"] == "RECOMENDADO"
    resp = await client.post(f"/api/runs/{run_id}/decision", json={"plan_id": run["plan"]["id"], "decision": "aprobar"})
    assert resp.json()["estado"] == "APROBADA"
    eventos = [Evento.model_validate(e) for e in (await client.get(f"/api/runs/{run_id}/auditoria")).json()]
    for e in eventos:
        validar_payload(e)
    assert any(e.tipo == TipoEvento.AGENTE_HERRAMIENTA and e.actor.endswith("agente-equipo") for e in eventos)
