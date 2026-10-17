from datetime import date

import pytest
from pydantic import ValidationError

from app.contract import (
    Alternativa,
    Control,
    DecisionHumana,
    EstadoControl,
    EstadoSistema,
    Evento,
    Evidencia,
    Requisito,
    ResultadoControl,
    ResultadoRequisito,
    RunCrear,
    TipoEvento,
    TipoRequisito,
    calcular_estado_sistema,
    consolidar_control,
    validar_payload,
)


def _control(bloqueante: bool = True, n: int = 2) -> Control:
    return Control(
        id="C1",
        nombre="Control",
        peligro_id="P1",
        bloqueante=bloqueante,
        requisitos=[
            Requisito(id=f"R{i}", tipo=TipoRequisito.EQUIPO, descripcion="x")
            for i in range(1, n + 1)
        ],
    )


def _res(req: str, estado: EstadoControl, con_evidencia: bool = True) -> ResultadoRequisito:
    evidencia = [Evidencia(registro="equipos/EQ-1", campo="estado", valor="operativo")]
    return ResultadoRequisito(
        control_id="C1",
        requisito_id=req,
        estado=estado,
        evidencia=evidencia if con_evidencia else [],
        verificado_por="capataz:agente-equipo",
    )


def _rc(estado: EstadoControl, bloqueante: bool = True) -> ResultadoControl:
    return ResultadoControl(control_id="C", bloqueante=bloqueante, estado=estado)


def test_gana_el_peor_estado():
    rc = consolidar_control(_control(), [_res("R1", EstadoControl.CUMPLE), _res("R2", EstadoControl.NO_CUMPLE)])
    assert rc.estado == EstadoControl.NO_CUMPLE


def test_todos_cumplen():
    rc = consolidar_control(_control(), [_res("R1", EstadoControl.CUMPLE), _res("R2", EstadoControl.CUMPLE)])
    assert rc.estado == EstadoControl.CUMPLE


def test_requisito_sin_resultado_no_es_cumple():
    rc = consolidar_control(_control(), [_res("R1", EstadoControl.CUMPLE)])
    assert rc.estado == EstadoControl.NO_VERIFICABLE
    assert len(rc.requisitos) == 2


def test_cumple_sin_evidencia_se_degrada():
    rc = consolidar_control(_control(n=1), [_res("R1", EstadoControl.CUMPLE, con_evidencia=False)])
    assert rc.estado == EstadoControl.NO_VERIFICABLE


def test_control_sin_requisitos_no_es_cumple():
    assert consolidar_control(_control(n=0), []).estado == EstadoControl.NO_VERIFICABLE


def test_bloqueante_incumplido_bloquea():
    assert calcular_estado_sistema([_rc(EstadoControl.CUMPLE), _rc(EstadoControl.NO_CUMPLE)]) == EstadoSistema.BLOQUEADO


def test_no_verificable_requiere_campo():
    assert calcular_estado_sistema([_rc(EstadoControl.CUMPLE), _rc(EstadoControl.NO_VERIFICABLE)]) == EstadoSistema.REQUIERE_CAMPO


def test_todo_cumple_recomendado():
    assert calcular_estado_sistema([_rc(EstadoControl.CUMPLE)]) == EstadoSistema.RECOMENDADO


def test_no_bloqueante_incumplido_no_bloquea():
    estado = calcular_estado_sistema([_rc(EstadoControl.CUMPLE), _rc(EstadoControl.NO_CUMPLE, bloqueante=False)])
    assert estado == EstadoSistema.RECOMENDADO


def test_sin_controles_no_recomienda():
    assert calcular_estado_sistema([]) == EstadoSistema.REQUIERE_CAMPO


def test_payload_invalido():
    evento = Evento(run_id="r", seq=1, tipo=TipoEvento.PLAN_LISTO, actor="sistema", payload={})
    with pytest.raises(ValidationError):
        validar_payload(evento)


def test_payload_valido():
    evento = Evento(run_id="r", seq=1, tipo=TipoEvento.RUN_ERROR, actor="sistema", payload={"mensaje": "x"})
    validar_payload(evento)


def test_rechazo_sin_comentario():
    with pytest.raises(ValidationError):
        DecisionHumana(plan_id="p", decision="rechazar", comentario="  ")
    DecisionHumana(plan_id="p", decision="aprobar")


def test_ronda_3_imposible():
    with pytest.raises(ValidationError):
        Alternativa(ronda=3)


def test_run_crear_exige_origen():
    with pytest.raises(ValidationError):
        RunCrear(modo="replay")
    with pytest.raises(ValidationError):
        RunCrear(modo="vivo")
    RunCrear(modo="vivo", escenario_id="E1")
