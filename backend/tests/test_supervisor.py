import asyncio
import time
from datetime import date

import httpx
import pytest
from pydantic_core import to_jsonable_python

from app.agents import supervisor as sup
from app.agents.alternativas import AlternativaPropuesta, CambioPropuesto, validar_propuestas
from app.agents.supervisor import Dependencias, confirmar_campo, ejecutar_run
from app.config import Settings
from app.contract import (
    ACTOR_EQUIPO, ACTOR_PERSONAL, ACTOR_RIESGO, Asignacion, Catalogo, Certificacion,
    ConfirmacionesCampo, Control, Equipo, Escenario, EstadoControl, EstadoSistema, Evento, Evidencia, Peligro,
    Persona, Requisito, RespuestaCampo, ResultadoRequisito, Run, Tarea, TipoEvento, TipoTarea, TurnoRef,
    validar_payload,
)
from app.llm import ClienteLLM, registrar_fake
from app.main import create_app
from app.store import MemoryStore

TURNO = TurnoRef(fecha=date(2026, 10, 20), turno="dia")
TAREA = Tarea(id="T-1", tipo_tarea="TT1", descripcion="roca inestable en galería 3", zona="G3", turno=TURNO,
              asignacion=Asignacion(personas=["PA"], equipos=["EQ-A"]))


def catalogo(campo=False):
    controles = [
        Control(id="C-EQ", nombre="Jumbo operativo", peligro_id="P1", aplica_a=["TT1"],
                requisitos=[Requisito(id="R-EQ", tipo="equipo", descripcion="Jumbo operativo", tipo_equipo="jumbo")]),
        Control(id="C-PER", nombre="Operador certificado", peligro_id="P1", aplica_a=["TT1"],
                requisitos=[Requisito(id="R-PER", tipo="competencia", descripcion="Certificado SOST",
                                      certificacion="SOST")]),
    ]
    if campo:
        controles.append(Control(id="C-CAMPO", nombre="Desatado previo", peligro_id="P1", aplica_a=["TT1"],
                                 requisitos=[Requisito(id="R-CAMPO", tipo="condicion_campo",
                                                       descripcion="Desatado realizado",
                                                       pregunta_campo="¿Se realizó el desatado?")]))
    return Catalogo(
        peligros=[Peligro(id="P1", nombre="Caída de rocas")],
        tipos_tarea=[TipoTarea(id="TT1", nombre="Sostenimiento")],
        controles=controles,
        personas=[Persona(id="PA", nombre="Ana"),
                  Persona(id="PB", nombre="Beto", certificaciones=[Certificacion(codigo="SOST", vence=date(2027, 1, 1))])],
        equipos=[Equipo(id="EQ-A", nombre="Jumbo A", tipo_equipo="jumbo", estado="mantenimiento"),
                 Equipo(id="EQ-B", nombre="Jumbo B", tipo_equipo="jumbo"),
                 Equipo(id="EQ-C", nombre="Jumbo C", tipo_equipo="jumbo", estado="fuera_servicio")],
        escenarios=[Escenario(id="E2", nombre="Conflicto", tarea=TAREA, resultado_esperado=EstadoSistema.RECOMENDADO,
                              escalamiento="Gerente de operaciones de la unidad")],
    )


class Emisor:
    """Como el runtime de P1: serializa y valida cada payload contra el contrato."""

    def __init__(self):
        self.eventos: list[Evento] = []

    async def __call__(self, tipo, actor, payload):
        ev = Evento(run_id="r1", seq=len(self.eventos) + 1, tipo=tipo, actor=actor, payload=to_jsonable_python(payload))
        validar_payload(ev)
        self.eventos.append(ev)
        return ev

    def tipos(self):
        return [e.tipo for e in self.eventos]

    def de_tipo(self, tipo):
        return [e for e in self.eventos if e.tipo == tipo]


def resultado(pedido, estado, detalle, actor):
    evidencia = [Evidencia(registro="reg/1", campo="estado", valor=detalle)] if estado != EstadoControl.NO_VERIFICABLE else []
    return ResultadoRequisito(control_id=pedido.control_id, requisito_id=pedido.requisito.id, estado=estado,
                              evidencia=evidencia, verificado_por=actor, detalle=detalle)


def mundo(ok_equipos=("EQ-B",), ok_personas=("PB",), pedidos=None, pausa=0.0):
    """Verificadores de prueba: cumplen si la asignación incluye un equipo/persona de la lista."""
    async def personal(sol, cat, emitir):
        await asyncio.sleep(pausa)
        pedidos is not None and pedidos.extend((r.control_id, r.requisito.id) for r in sol.requisitos)
        ok = bool(set(ok_personas) & set(sol.tarea.asignacion.personas))
        return [resultado(r, EstadoControl.CUMPLE if ok else EstadoControl.NO_CUMPLE,
                          "Certificación vigente" if ok else "Sin certificación vigente", ACTOR_PERSONAL)
                for r in sol.requisitos]

    async def equipo(sol, cat, emitir):
        await asyncio.sleep(pausa)
        pedidos is not None and pedidos.extend((r.control_id, r.requisito.id) for r in sol.requisitos)
        ok = bool(set(ok_equipos) & set(sol.tarea.asignacion.equipos))
        return [resultado(r, EstadoControl.CUMPLE if ok else EstadoControl.NO_CUMPLE,
                          "Equipo operativo" if ok else "Equipo en mantenimiento", ACTOR_EQUIPO)
                for r in sol.requisitos]

    return personal, equipo


def deps(verificadores, **kw):
    personal, equipo = verificadores
    return Dependencias(verificar_personal=personal, verificar_equipo=equipo, buscar=lambda cat, **k: [],
                        cliente=ClienteLLM(modo="fake"), **kw)


def correr(cat, d, tarea=TAREA, escenario_id="E2"):
    emisor = Emisor()
    run = Run(id="r1", tarea=tarea, escenario_id=escenario_id)
    plan = asyncio.run(ejecutar_run(run, cat, emisor, deps=d))
    return plan, emisor


# -- E1: caso limpio ---------------------------------------------------------------------------

def test_e1_limpio_secuencia_de_eventos_y_plan_recomendado():
    plan, emisor = correr(catalogo(), deps(mundo(ok_equipos=("EQ-A",), ok_personas=("PA",))))
    tipos = emisor.tipos()
    assert tipos[0] == TipoEvento.RUN_INICIADO
    assert tipos[-3:] == [TipoEvento.SUPERVISOR_CONSOLIDADO, TipoEvento.PLAN_LISTO, TipoEvento.HUMANO_DECISION_REQUERIDA]
    assert plan.estado_sistema == EstadoSistema.RECOMENDADO and plan.cambios == []
    orden = [(e.tipo, e.actor) for e in emisor.eventos]
    assert orden.index((TipoEvento.AGENTE_COMPLETADO, ACTOR_RIESGO)) < orden.index((TipoEvento.AGENTE_INICIADO, ACTOR_PERSONAL))
    for actor in (ACTOR_RIESGO, ACTOR_PERSONAL, ACTOR_EQUIPO):
        assert (TipoEvento.AGENTE_INICIADO, actor) in orden and (TipoEvento.AGENTE_COMPLETADO, actor) in orden
    decision = emisor.eventos[-1].payload
    assert decision == {"plan_id": plan.id, "solo_rechazo": False}
    assert [e.seq for e in emisor.eventos] == list(range(1, len(tipos) + 1))


def test_cada_requisito_se_reparte_exactamente_una_vez():
    pedidos: list = []
    correr(catalogo(campo=True), deps(mundo(ok_equipos=("EQ-A",), ok_personas=("PA",), pedidos=pedidos)))
    assert sorted(pedidos) == [("C-EQ", "R-EQ"), ("C-PER", "R-PER")]  # el de campo no va a ningún agente


def test_personal_y_equipo_corren_en_paralelo():
    inicio = time.perf_counter()
    correr(catalogo(), deps(mundo(ok_equipos=("EQ-A",), ok_personas=("PA",), pausa=0.3)))
    assert time.perf_counter() - inicio < 0.55  # ≈ máx, no suma


# -- fallos de agente ---------------------------------------------------------------------------

def test_agente_que_lanza_excepcion_deja_sus_requisitos_no_verificables_sin_colgar_el_run():
    personal, _ = mundo(ok_equipos=("EQ-A",), ok_personas=("PA",))

    async def roto(sol, cat, emitir):
        raise RuntimeError("equipo caído")

    plan, emisor = correr(catalogo(), deps((personal, roto)))
    por_control = {rc.control_id: rc.estado for rc in plan.resultados}
    assert por_control == {"C-EQ": EstadoControl.NO_VERIFICABLE, "C-PER": EstadoControl.CUMPLE}
    assert plan.estado_sistema == EstadoSistema.REQUIERE_CAMPO
    assert emisor.tipos()[-1] == TipoEvento.HUMANO_DECISION_REQUERIDA
    assert emisor.eventos[-1].payload["solo_rechazo"] is True  # nada que confirmar en campo: solo rechazar


def test_agente_que_excede_el_tiempo_limite_no_cuelga_el_run():
    _, equipo = mundo(ok_equipos=("EQ-A",), ok_personas=("PA",))
    personal_lento, _ = mundo(pausa=5)
    inicio = time.perf_counter()
    plan, _ = correr(catalogo(), deps((personal_lento, equipo), agente_timeout_s=0.1))
    assert time.perf_counter() - inicio < 2
    assert {rc.control_id: rc.estado for rc in plan.resultados}["C-PER"] == EstadoControl.NO_VERIFICABLE


def test_un_agente_que_devuelve_cumple_sin_evidencia_no_logra_un_cumple():
    async def sin_evidencia(sol, cat, emitir):
        return [ResultadoRequisito(control_id=r.control_id, requisito_id=r.requisito.id, estado=EstadoControl.CUMPLE,
                                   verificado_por=ACTOR_PERSONAL) for r in sol.requisitos]

    _, equipo = mundo(ok_equipos=("EQ-A",))
    plan, _ = correr(catalogo(), deps((sin_evidencia, equipo)))
    assert {rc.control_id: rc.estado for rc in plan.resultados}["C-PER"] == EstadoControl.NO_VERIFICABLE


# -- campo (E2c) ---------------------------------------------------------------------------------

def test_condicion_de_campo_pide_confirmacion_y_al_confirmarla_se_recomienda():
    cat = catalogo(campo=True)
    d = deps(mundo(ok_equipos=("EQ-A",), ok_personas=("PA",)))
    plan, emisor = correr(cat, d)
    assert plan.estado_sistema == EstadoSistema.REQUIERE_CAMPO
    assert emisor.tipos()[-2:] == [TipoEvento.PLAN_LISTO, TipoEvento.HUMANO_CAMPO_REQUERIDO]
    preguntas = emisor.eventos[-1].payload["preguntas"]
    assert [(p["requisito_id"], p["pregunta"]) for p in preguntas] == [("R-CAMPO", "¿Se realizó el desatado?")]

    run = Run(id="r1", tarea=TAREA, escenario_id="E2", plan=plan)
    conf = ConfirmacionesCampo(usuario="ana", respuestas=[RespuestaCampo(requisito_id="R-CAMPO", cumple=True, nota="listo")])
    emisor2 = Emisor()
    final = asyncio.run(confirmar_campo(run, cat, conf, emisor2, deps=d))
    assert final.estado_sistema == EstadoSistema.RECOMENDADO and final.id == plan.id
    assert emisor2.tipos() == [TipoEvento.SUPERVISOR_CONSOLIDADO, TipoEvento.PLAN_LISTO, TipoEvento.HUMANO_DECISION_REQUERIDA]
    campo = [rr for rc in final.resultados for rr in rc.requisitos if rr.requisito_id == "R-CAMPO"][0]
    assert campo.estado == EstadoControl.CUMPLE and campo.evidencia and campo.verificado_por == "humano:ana"


def test_campo_a_medias_vuelve_a_preguntar_lo_pendiente():
    cat = catalogo(campo=True)
    d = deps(mundo(ok_equipos=("EQ-A",), ok_personas=("PA",)))
    plan, _ = correr(cat, d)
    emisor = Emisor()
    final = asyncio.run(confirmar_campo(Run(id="r1", tarea=TAREA, plan=plan), cat, ConfirmacionesCampo(), emisor, deps=d))
    assert final.estado_sistema == EstadoSistema.REQUIERE_CAMPO
    assert emisor.tipos()[-1] == TipoEvento.HUMANO_CAMPO_REQUERIDO


def test_un_no_cumple_en_campo_entra_al_flujo_de_conflicto():
    cat = catalogo(campo=True)
    d = deps(mundo(ok_equipos=("EQ-A",), ok_personas=("PA",)))
    plan, _ = correr(cat, d)
    conf = ConfirmacionesCampo(respuestas=[RespuestaCampo(requisito_id="R-CAMPO", cumple=False, nota="sin desatar")])
    emisor = Emisor()
    asyncio.run(confirmar_campo(Run(id="r1", tarea=TAREA, escenario_id="E2", plan=plan), cat, conf, emisor, deps=d))
    conflicto = emisor.de_tipo(TipoEvento.CONFLICTO_DETECTADO)[0].payload
    assert (conflicto["control_id"], conflicto["requisito_id"]) == ("C-CAMPO", "R-CAMPO")
    assert conflicto["evidencia"][0]["valor"].startswith("no")
    assert emisor.tipos()[-1] in (TipoEvento.HUMANO_DECISION_REQUERIDA, TipoEvento.HUMANO_CAMPO_REQUERIDO)


# -- E2: conflicto y alternativas ------------------------------------------------------------------

def test_e2_conflicto_alternativa_verificada_por_herramientas():
    plan, emisor = correr(catalogo(), deps(mundo()))  # el plan original (EQ-A, PA) no cumple
    tipos = emisor.tipos()
    assert emisor.de_tipo(TipoEvento.SUPERVISOR_CONSOLIDADO)[0].payload["estado_sistema"] == "BLOQUEADO"
    assert len(emisor.de_tipo(TipoEvento.CONFLICTO_DETECTADO)) == 2
    assert tipos.index(TipoEvento.CONFLICTO_DETECTADO) < tipos.index(TipoEvento.CONFLICTO_ALTERNATIVAS) \
        < tipos.index(TipoEvento.CONFLICTO_ALTERNATIVA_VERIFICADA) < tipos.index(TipoEvento.PLAN_LISTO)

    verificada = emisor.de_tipo(TipoEvento.CONFLICTO_ALTERNATIVA_VERIFICADA)[0].payload["alternativa"]
    assert verificada["cumple_bloqueantes"] is True and verificada["motivo_fallo"] is None
    assert verificada["explicacion"] and verificada["ronda"] == 1  # explicación del LLM, separada del veredicto

    listo = emisor.de_tipo(TipoEvento.PLAN_LISTO)[0].payload
    assert listo["plan"]["estado_sistema"] == "BLOQUEADO"
    alternativo = listo["planes_alternativos"][0]
    assert alternativo["id"] == verificada["id"] and alternativo["estado_sistema"] == "RECOMENDADO"
    assert {(c["tipo"], c["desde"], c["hacia"]) for c in alternativo["cambios"]} == {
        ("equipo_equivalente", "EQ-A", "EQ-B"), ("certificacion_equivalente", "PA", "PB")}
    assert alternativo["asignacion"] == {"personas": ["PB"], "equipos": ["EQ-B"]}
    assert emisor.eventos[-1].payload == {"plan_id": alternativo["id"], "solo_rechazo": False}
    assert plan.id == alternativo["id"]


def test_alternativa_que_el_llm_cree_valida_pero_las_herramientas_rechazan():
    async def cree_valida(ctx):
        return {"alternativas": [{"cambios": [{"tipo": "equipo_equivalente", "desde": "EQ-A", "hacia": "EQ-C"},
                                              {"tipo": "certificacion_equivalente", "desde": "PA", "hacia": "PB"}],
                                  "explicacion": "EQ-C parece servir."}]}

    registrar_fake("alternativas", cree_valida, escenario_id="CREE")
    plan, emisor = correr(catalogo(), deps(mundo()), escenario_id="CREE")  # solo EQ-B cumple, no EQ-C
    primera = emisor.de_tipo(TipoEvento.CONFLICTO_ALTERNATIVA_VERIFICADA)[0].payload["alternativa"]
    assert primera["cumple_bloqueantes"] is False
    assert "Equipo en mantenimiento" in primera["motivo_fallo"]


def test_la_ronda_2_recibe_los_motivos_de_fallo_de_la_ronda_1():
    vistos: list = []

    async def propone(ctx):
        vistos.append((ctx.contexto["ronda"], list(ctx.contexto["motivos_previos"])))
        return {"alternativas": [{"cambios": [{"tipo": "equipo_equivalente", "desde": "EQ-A",
                                               "hacia": "EQ-C" if ctx.contexto["ronda"] == 1 else "EQ-B"}],
                                  "explicacion": "x"}]}

    registrar_fake("alternativas", propone, escenario_id="RONDAS")
    correr(catalogo(), deps(mundo(ok_personas=("PA",))), escenario_id="RONDAS")
    assert [r for r, _ in vistos] == [1, 2]
    assert vistos[0][1] == [] and "Equipo en mantenimiento" in vistos[1][1][0]


# -- E3: sin alternativa segura ---------------------------------------------------------------------

def test_e3_sin_alternativa_segura_bloquea_con_escalamiento_y_solo_dos_rondas():
    plan, emisor = correr(catalogo(), deps(mundo(ok_equipos=(), ok_personas=())))
    rondas = [e.payload["ronda"] for e in emisor.de_tipo(TipoEvento.CONFLICTO_ALTERNATIVAS)]
    assert rondas == [1, 2]
    assert all(not e.payload["alternativa"]["cumple_bloqueantes"]
               for e in emisor.de_tipo(TipoEvento.CONFLICTO_ALTERNATIVA_VERIFICADA))
    assert plan.estado_sistema == EstadoSistema.BLOQUEADO
    assert plan.escalamiento == "Gerente de operaciones de la unidad"
    assert "Sin alternativa segura" in plan.motivo
    assert emisor.de_tipo(TipoEvento.PLAN_LISTO)[0].payload["planes_alternativos"] == []
    assert emisor.eventos[-1].payload == {"plan_id": plan.id, "solo_rechazo": True}


def test_sin_escenario_el_escalamiento_es_generico():
    plan, _ = correr(catalogo(), deps(mundo(ok_equipos=(), ok_personas=())), escenario_id=None)
    assert plan.escalamiento == sup.ESCALAMIENTO_GENERICO


def test_si_el_llm_de_alternativas_falla_no_se_inventan_alternativas():
    from app.llm import LLMError

    class Roto(ClienteLLM):
        async def completar(self, **kw):
            if kw["agente"] == "alternativas":
                raise LLMError("sin red")
            return await super().completar(**kw)

    d = deps(mundo(ok_equipos=(), ok_personas=()))
    d.cliente = Roto(modo="fake")
    plan, emisor = correr(catalogo(), d)
    assert emisor.de_tipo(TipoEvento.CONFLICTO_ALTERNATIVAS) == []
    assert plan.estado_sistema == EstadoSistema.BLOQUEADO and emisor.eventos[-1].payload["solo_rechazo"] is True


# -- validación de lo que propone el LLM ---------------------------------------------------------------

@pytest.mark.parametrize("cambio, esperado", [
    (CambioPropuesto(tipo="equipo_equivalente", desde="EQ-A", hacia="EQ-X"), "equipo inexistente"),
    (CambioPropuesto(tipo="certificacion_equivalente", desde="PA", hacia="PX"), "persona inexistente"),
    (CambioPropuesto(tipo="equipo_equivalente", desde="EQ-B", hacia="EQ-C"), "no está asignado"),
    (CambioPropuesto(tipo="eliminar_requisito", desde="R-EQ", hacia=""), "tipo de cambio no permitido"),
    (CambioPropuesto(tipo="relajar_requisito", desde="R-PER", hacia=""), "tipo de cambio no permitido"),
    (CambioPropuesto(tipo="reprogramar_turno", desde="2026-10-20/dia", hacia="mañana"), "turno inválido"),
    (CambioPropuesto(tipo="reprogramar_turno", desde="2026-10-19/dia", hacia="2026-10-21/dia"), "no es el turno actual"),
])
def test_propuestas_con_ids_inventados_o_que_quitan_requisitos_se_descartan(cambio, esperado):
    validas, descartes = validar_propuestas([AlternativaPropuesta(cambios=[cambio])], TAREA, catalogo(), 1, set())
    assert validas == [] and esperado in descartes[0]


def test_propuestas_vacias_repetidas_y_el_tope_de_tres():
    ok = lambda hacia: AlternativaPropuesta(cambios=[CambioPropuesto(tipo="equipo_equivalente", desde="EQ-A", hacia=hacia)])
    cat = catalogo()
    vistas: set = set()
    validas, descartes = validar_propuestas([AlternativaPropuesta(), ok("EQ-B"), ok("EQ-B")], TAREA, cat, 1, vistas)
    assert len(validas) == 1 and "sin cambios" in descartes[0] and "repite" in descartes[1]
    de_nuevo, _ = validar_propuestas([ok("EQ-B")], TAREA, cat, 2, vistas)
    assert de_nuevo == []  # no repite entre rondas


# -- integración con la API de P1 --------------------------------------------------------------------------

@pytest.fixture
async def client(tmp_path, monkeypatch):
    s = Settings()
    s.data_dir, s.replays_dir, s.memory_dump_dir = tmp_path / "vacio", tmp_path / "replays", tmp_path / "memoria"
    s.store_backend = "memory"
    # Verificadores de prueba para el seed de juguete de P1 (E1): todo cumple lo verificable.
    personal, equipo = mundo(ok_equipos=("EQ-JUG-01",), ok_personas=("PER-JUG-01",))
    monkeypatch.setattr(sup, "dependencias_por_defecto", lambda: deps((personal, equipo)))
    app = create_app(s, MemoryStore(data_dir=s.data_dir, dump_dir=s.memory_dump_dir))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _estado(client, run_id, estado):
    for _ in range(300):
        run = (await client.get(f"/api/runs/{run_id}")).json()
        if run["estado"] == estado:
            return run
        await asyncio.sleep(0.01)
    raise AssertionError(f"El run quedó en {run['estado']}, no en {estado}")


async def test_api_e1_de_punta_a_punta_con_el_supervisor_real(client):
    assert (await client.get("/api/health")).json()["orquestador"] == "p2"
    run_id = (await client.post("/api/runs", json={"escenario_id": "E1"})).json()["run_id"]
    await _estado(client, run_id, "ESPERANDO_CAMPO")
    await client.post(f"/api/runs/{run_id}/campo",
                      json={"usuario": "ana", "respuestas": [{"requisito_id": "REQ-JUG-03", "cumple": True}]})
    run = await _estado(client, run_id, "ESPERANDO_DECISION")
    assert run["plan"]["estado_sistema"] == "RECOMENDADO"
    resp = await client.post(f"/api/runs/{run_id}/decision", json={"plan_id": run["plan"]["id"], "decision": "aprobar"})
    assert resp.json()["estado"] == "APROBADA"

    eventos = [Evento.model_validate(e) for e in (await client.get(f"/api/runs/{run_id}/auditoria")).json()]
    assert [e.seq for e in eventos] == list(range(1, len(eventos) + 1))
    for e in eventos:
        validar_payload(e)
    assert eventos[-1].tipo == TipoEvento.RUN_FINALIZADO
