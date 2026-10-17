import asyncio
from datetime import date

from p3_datos import NOCHE, catalogo_p3, tarea
from pydantic_core import to_jsonable_python

from app.agents.equipo import verificar_equipo
from app.agents.personal import verificar_personal
from app.contract import (
    ACTOR_EQUIPO, ACTOR_PERSONAL, AgenteSolicitud, EstadoControl, Evento, RequisitoAVerificar, TipoEvento, TurnoRef,
    validar_payload,
)

CAT = catalogo_p3()


class Emisor:
    def __init__(self):
        self.eventos: list[Evento] = []

    async def __call__(self, tipo, actor, payload):
        ev = Evento(run_id="r", seq=len(self.eventos) + 1, tipo=tipo, actor=actor, payload=to_jsonable_python(payload))
        validar_payload(ev)  # como el runtime de P1
        self.eventos.append(ev)
        return ev

    def trazas(self):
        return [e.payload["trace"] for e in self.eventos]


def solicitud(control_id, agente, tarea_, equivalencias=False):
    control = CAT.control(control_id)
    return AgenteSolicitud(agente=agente, tarea=tarea_, permitir_equivalencias=equivalencias,
                           requisitos=[RequisitoAVerificar(control_id=control_id, requisito=r) for r in control.requisitos])


def personal(tarea_, equivalencias=False, control="CTL-OPER"):
    emisor = Emisor()
    res = asyncio.run(verificar_personal(solicitud(control, ACTOR_PERSONAL, tarea_, equivalencias), CAT, emisor))
    return res, emisor


def equipo(tarea_, equivalencias=False, control="CTL-EMP"):
    emisor = Emisor()
    res = asyncio.run(verificar_equipo(solicitud(control, ACTOR_EQUIPO, tarea_, equivalencias), CAT, emisor))
    return res, emisor


# -- Personal -----------------------------------------------------------------------------------

def test_personal_cumple_con_evidencia_y_trazas():
    (r,), emisor = personal(tarea(["PER-1"], ["EQ-1"]))
    assert (r.control_id, r.requisito_id, r.estado, r.verificado_por) == ("CTL-OPER", "REQ-CERT", EstadoControl.CUMPLE, ACTOR_PERSONAL)
    assert {e.registro for e in r.evidencia} == {"personas/PER-1"} and len(r.evidencia) == 2
    assert [t["nombre"] for t in emisor.trazas()] == ["personal_disponible", "verificar_certificacion", "detectar_doble_asignacion"]
    assert all(t["salida_resumen"] and t["entrada"] for t in emisor.trazas())
    assert {e.tipo for e in emisor.eventos} == {TipoEvento.AGENTE_HERRAMIENTA}  # iniciado/completado son de P2
    assert {e.actor for e in emisor.eventos} == {ACTOR_PERSONAL}


def test_certificacion_vencida_no_cuenta():
    (r,), _ = personal(tarea(["PER-2"], ["EQ-1"]))
    assert r.estado == EstadoControl.NO_CUMPLE and "venció el 30/09/2026" in r.detalle and r.evidencia


def test_persona_no_disponible_en_el_turno():
    (r,), _ = personal(tarea(["PER-1"], ["EQ-1"], turno=TurnoRef(fecha=date(2026, 10, 21), turno="dia")))
    assert r.estado == EstadoControl.NO_CUMPLE and "no está disponible" in r.detalle
    assert r.evidencia[-1].campo == "turnos"


def test_doble_asignacion_es_no_cumple_con_la_otra_tarea_como_evidencia():
    (r,), emisor = personal(tarea(["PER-5"], ["EQ-1"]))  # tiene SOST vigente, pero está ocupada
    assert r.estado == EstadoControl.NO_CUMPLE and "ya está asignada a TA-OCUPA" in r.detalle
    assert r.evidencia[-1].registro == "tareas/TA-OCUPA"
    assert "detectar_doble_asignacion" in [t["nombre"] for t in emisor.trazas()]


def test_primera_pasada_estricta_y_equivalencias_en_alternativas():
    libre = tarea(["PER-3"], ["EQ-1"], turno=NOCHE)  # PER-3 solo tiene SOST-B y está libre de noche
    assert personal(libre)[0][0].estado == EstadoControl.NO_CUMPLE
    assert personal(libre, equivalencias=True)[0][0].estado == EstadoControl.CUMPLE


def test_con_varias_asignadas_basta_una_competente():
    (r,), _ = personal(tarea(["PER-2", "PER-1"], ["EQ-1"]))
    assert r.estado == EstadoControl.CUMPLE and r.evidencia[0].registro == "personas/PER-1"


def test_sin_personal_asignado_no_cumple():
    (r,), _ = personal(tarea([], ["EQ-1"]))
    assert r.estado == EstadoControl.NO_CUMPLE and r.evidencia[0].registro == "tareas/TA-X"


def test_persona_fuera_del_catalogo_es_no_verificable_y_nunca_cumple():
    (r,), _ = personal(tarea(["PER-99"], ["EQ-1"]))
    assert r.estado == EstadoControl.NO_VERIFICABLE and "PER-99" in r.detalle
    (r2,), _ = personal(tarea(["PER-99", "PER-2"], ["EQ-1"]))
    assert r2.estado == EstadoControl.NO_CUMPLE  # una evaluable que no cumple ⇒ incumplimiento comprobado


def test_requisitos_que_no_son_de_competencia_quedan_no_verificables():
    (r,), _ = personal(tarea(["PER-1"], ["EQ-1"]), control="CTL-EMP")
    assert r.estado == EstadoControl.NO_VERIFICABLE


def test_la_doble_asignacion_se_consulta_una_vez_por_persona():
    sol = solicitud("CTL-OPER", ACTOR_PERSONAL, tarea(["PER-1"], ["EQ-1"]))
    sol.requisitos = sol.requisitos * 2
    emisor = Emisor()
    resultados = asyncio.run(verificar_personal(sol, CAT, emisor))
    assert len(resultados) == 2 and all(r.estado == EstadoControl.CUMPLE for r in resultados)
    assert [t["nombre"] for t in emisor.trazas()].count("detectar_doble_asignacion") == 1


def test_un_cumple_siempre_trae_evidencia():
    for pers in (["PER-1"], ["PER-2", "PER-1"]):
        (r,), _ = personal(tarea(pers, ["EQ-1"]))
        assert r.estado != EstadoControl.CUMPLE or r.evidencia


# -- Equipo ---------------------------------------------------------------------------------------

def test_equipo_cumple_con_evidencia_y_trazas():
    (r,), emisor = equipo(tarea(["PER-1"], ["EQ-1"]))
    assert (r.estado, r.verificado_por) == (EstadoControl.CUMPLE, ACTOR_EQUIPO)
    assert [e.campo for e in r.evidencia] == ["tipo_equipo", "estado"] and {e.registro for e in r.evidencia} == {"equipos/EQ-1"}
    assert [t["nombre"] for t in emisor.trazas()] == ["verificar_tipo_equipo", "consultar_estado_equipo"]
    assert {e.actor for e in emisor.eventos} == {ACTOR_EQUIPO}


def test_equipo_en_mantenimiento_no_cumple_con_el_registro_del_equipo():
    (r,), _ = equipo(tarea(["PER-1"], ["EQ-2"]))
    assert r.estado == EstadoControl.NO_CUMPLE
    assert r.detalle == "Ningún equipo asignado está disponible: Empernador 2 está en mantenimiento"
    assert (r.evidencia[0].registro, r.evidencia[0].campo, r.evidencia[0].valor) == ("equipos/EQ-2", "estado", "mantenimiento")


def test_primera_pasada_ignora_los_tipos_equivalentes():
    (r,), _ = equipo(tarea(["PER-1"], ["EQ-3"]))
    assert r.estado == EstadoControl.NO_CUMPLE and "es del tipo perforadora, no empernador" in r.detalle
    assert r.evidencia[0].registro == "tareas/TA-X"


def test_en_alternativas_el_equipo_equivalente_cuenta_si_esta_libre():
    assert equipo(tarea(["PER-1"], ["EQ-3"]), equivalencias=True)[0][0].estado == EstadoControl.CUMPLE
    (r,), _ = equipo(tarea(["PER-1"], ["EQ-3"], turno=NOCHE), equivalencias=True)  # mantenimiento programado de noche
    assert r.estado == EstadoControl.NO_CUMPLE and "programado" in r.detalle


def test_con_varios_equipos_basta_uno_utilizable():
    (r,), _ = equipo(tarea(["PER-1"], ["EQ-2", "EQ-1"]))
    assert r.estado == EstadoControl.CUMPLE and r.evidencia[0].registro == "equipos/EQ-1"


def test_sin_equipo_asignado_o_fuera_del_catalogo():
    assert equipo(tarea(["PER-1"], []))[0][0].estado == EstadoControl.NO_CUMPLE
    (r,), _ = equipo(tarea(["PER-1"], ["EQ-99"]))
    assert r.estado == EstadoControl.NO_VERIFICABLE and "EQ-99" in r.detalle


def test_requisito_que_no_es_de_equipo_queda_no_verificable():
    assert equipo(tarea(["PER-1"], ["EQ-1"]), control="CTL-OPER")[0][0].estado == EstadoControl.NO_VERIFICABLE
