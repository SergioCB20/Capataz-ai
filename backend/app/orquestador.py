"""Punto de entrada al orquestador de P2, con stub de P1 mientras no exista.

En cuanto exista `app/agents/supervisor.py` (P2), se usa ese. El stub solo
sirve para desarrollar la API y la UI; nunca marca un CUMPLE sin evidencia.
"""

from __future__ import annotations

import importlib
import logging
from typing import Awaitable, Callable

from app.contract import (
    ACTOR_EQUIPO,
    ACTOR_PERSONAL,
    ACTOR_RIESGO,
    ACTOR_SUPERVISOR,
    ACTOR_SISTEMA,
    Catalogo,
    ConfirmacionesCampo,
    Emitir,
    EstadoControl,
    EstadoSistema,
    EvaluacionRiesgo,
    Evidencia,
    Fuente,
    PeligroDetectado,
    Plan,
    PreguntaCampo,
    ResultadoRequisito,
    Run,
    TipoEvento,
    TipoFuente,
    calcular_estado_sistema,
    consolidar_control,
)

log = logging.getLogger(__name__)

EjecutarRun = Callable[[Run, Catalogo, Emitir], Awaitable[Plan]]
ConfirmarCampo = Callable[[Run, Catalogo, ConfirmacionesCampo, Emitir], Awaitable[Plan]]


def obtener_orquestador() -> tuple[EjecutarRun, ConfirmarCampo, str]:
    """Devuelve (ejecutar_run, confirmar_campo, origen) con origen "p2" o "stub"."""
    try:
        supervisor = importlib.import_module("app.agents.supervisor")
    except ModuleNotFoundError as e:
        if e.name in ("app.agents", "app.agents.supervisor"):
            return ejecutar_run_stub, confirmar_campo_stub, "stub"
        raise  # un import roto dentro de P2 debe verse, no tapar con el stub
    return supervisor.ejecutar_run, supervisor.confirmar_campo, "p2"


# ---------------------------------------------------------------------------
# Stub (P1): flujo mínimo que pasa por campo para cerrar el circuito
# ---------------------------------------------------------------------------


def _controles_aplicables(run: Run, catalogo: Catalogo):
    return [c for c in catalogo.controles if run.tarea.tipo_tarea in c.aplica_a]


async def ejecutar_run_stub(run: Run, catalogo: Catalogo, emitir: Emitir) -> Plan:
    await emitir(TipoEvento.RUN_INICIADO, ACTOR_SISTEMA, {"tarea": run.tarea})
    controles = _controles_aplicables(run, catalogo)

    await emitir(TipoEvento.AGENTE_INICIADO, ACTOR_RIESGO, {"agente": ACTOR_RIESGO})
    evaluacion = EvaluacionRiesgo(
        peligros=[
            PeligroDetectado(
                peligro_id=pid,
                justificacion="Stub de P1: controles del catálogo por tipo de tarea",
                controles=[c.id for c in controles if c.peligro_id == pid],
            )
            for pid in sorted({c.peligro_id for c in controles})
        ]
    )
    await emitir(
        TipoEvento.AGENTE_COMPLETADO,
        ACTOR_RIESGO,
        {"agente": ACTOR_RIESGO, "resumen": f"{len(controles)} controles aplicables", "evaluacion": evaluacion},
    )

    for actor in (ACTOR_PERSONAL, ACTOR_EQUIPO):
        await emitir(TipoEvento.AGENTE_INICIADO, actor, {"agente": actor})
        await emitir(
            TipoEvento.AGENTE_COMPLETADO,
            actor,
            {"agente": actor, "resumen": "Stub de P1: sin verificación real", "resultados": []},
        )

    resultados = [consolidar_control(c, []) for c in controles]
    estado = calcular_estado_sistema(resultados)
    await emitir(
        TipoEvento.SUPERVISOR_CONSOLIDADO,
        ACTOR_SUPERVISOR,
        {"resultados": resultados, "estado_sistema": estado},
    )
    plan = Plan(run_id=run.id, estado_sistema=estado, asignacion=run.tarea.asignacion, resultados=resultados)
    preguntas = [
        PreguntaCampo(
            requisito_id=r.requisito_id,
            control_id=r.control_id,
            pregunta=_pregunta(catalogo, r.control_id, r.requisito_id),
        )
        for rc in resultados
        for r in rc.requisitos
        if r.estado == EstadoControl.NO_VERIFICABLE
    ]
    if preguntas:
        await emitir(TipoEvento.HUMANO_CAMPO_REQUERIDO, ACTOR_SUPERVISOR, {"preguntas": preguntas})
        return plan
    return await _cerrar_plan(plan, emitir)


async def confirmar_campo_stub(
    run: Run, catalogo: Catalogo, conf: ConfirmacionesCampo, emitir: Emitir
) -> Plan:
    respuestas = {r.requisito_id: r for r in conf.respuestas}
    resultados = []
    for control in _controles_aplicables(run, catalogo):
        verificados = [
            ResultadoRequisito(
                control_id=control.id,
                requisito_id=req.id,
                estado=EstadoControl.CUMPLE if respuestas[req.id].cumple else EstadoControl.NO_CUMPLE,
                evidencia=[
                    Evidencia(
                        registro="confirmacion_campo",
                        campo=req.id,
                        valor=respuestas[req.id].nota or ("sí" if respuestas[req.id].cumple else "no"),
                        fuente=Fuente(tipo=TipoFuente.SIMULADO, referencia=f"Confirmado por {conf.usuario}"),
                    )
                ],
                verificado_por=f"humano:{conf.usuario}",
            )
            for req in control.requisitos
            if req.id in respuestas
        ]
        resultados.append(consolidar_control(control, verificados))
    estado = calcular_estado_sistema(resultados)
    await emitir(
        TipoEvento.SUPERVISOR_CONSOLIDADO,
        ACTOR_SUPERVISOR,
        {"resultados": resultados, "estado_sistema": estado},
    )
    plan = Plan(run_id=run.id, estado_sistema=estado, asignacion=run.tarea.asignacion, resultados=resultados)
    return await _cerrar_plan(plan, emitir)


async def _cerrar_plan(plan: Plan, emitir: Emitir) -> Plan:
    await emitir(TipoEvento.PLAN_LISTO, ACTOR_SUPERVISOR, {"plan": plan})
    await emitir(
        TipoEvento.HUMANO_DECISION_REQUERIDA,
        ACTOR_SUPERVISOR,
        {"plan_id": plan.id, "solo_rechazo": plan.estado_sistema == EstadoSistema.BLOQUEADO},
    )
    return plan


def _pregunta(catalogo: Catalogo, control_id: str, requisito_id: str) -> str:
    control = catalogo.control(control_id)
    req = next((r for r in control.requisitos if r.id == requisito_id), None) if control else None
    if req and req.pregunta_campo:
        return req.pregunta_campo
    return f"¿Se cumple: {req.descripcion if req else requisito_id}?"
