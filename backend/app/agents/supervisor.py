"""Supervisor (P2): orquesta el run. Es código determinista; el LLM solo interviene en Riesgo y
en las alternativas (RT-01). Puntos de entrada que llama P1: `ejecutar_run` y `confirmar_campo`.

Flujo: Riesgo → reparto de requisitos → Personal ‖ Equipo → consolidación → (conflicto: hasta
2 rondas de alternativas re-verificadas con herramientas) → plan → campo o decisión humana.

Convenciones con el resto del equipo:
- Plan alternativo: `Plan.id == Alternativa.id`, para que la UI los relacione.
- `plan.listo`: `plan` es el original (puede ser BLOQUEADO) y `planes_alternativos` los verificados,
  el mejor primero. `decision_requerida.plan_id` apunta al mejor candidato.
- Solo se puede aprobar un plan RECOMENDADO; si el mejor candidato no lo es y no hay nada que
  confirmar en campo, la decisión es solo rechazo.
"""
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.agents import _p3
from app.agents._contrato import (
    ACTOR_EQUIPO, ACTOR_PERSONAL, ACTOR_RIESGO, ACTOR_SISTEMA, ACTOR_SUPERVISOR, AgenteSolicitud,
    Alternativa, Catalogo, Control, ConfirmacionesCampo, Emitir, EstadoControl, EstadoSistema, EvaluacionRiesgo,
    Evidencia, Fuente, PayloadAlternativaVerificada, PayloadConflictoAlternativas, PayloadConflictoDetectado,
    PayloadPlanListo, Plan, PreguntaCampo, RequisitoAVerificar, ResultadoControl, ResultadoRequisito, Run,
    TipoEvento, TipoFuente, TipoRequisito, actor_humano, calcular_estado_sistema, consolidar_control,
)
from app.agents.alternativas import aplicar_cambios, describir, proponer_alternativas
from app.agents.riesgo import controles_exigidos, evaluar_riesgo, filtrar_y_completar
from app.llm import ClienteLLM

log = logging.getLogger("capataz.supervisor")

Verificador = Callable[[AgenteSolicitud, Catalogo, Emitir], Awaitable[list[ResultadoRequisito]]]

ESCALAMIENTO_GENERICO = "Escalar al supervisor responsable de la tarea para replanificarla."


@dataclass
class Dependencias:
    """Lo que el Supervisor usa de otros; se inyecta en las pruebas."""
    verificar_personal: Verificador
    verificar_equipo: Verificador
    buscar: Callable[..., Any]
    cliente: ClienteLLM | None = None
    agente_timeout_s: float = 30.0   # Personal y Equipo (RF-F1-07)
    riesgo_timeout_s: float = 45.0   # Agente Riesgo, incluye el LLM


def dependencias_por_defecto() -> Dependencias:
    return Dependencias(
        verificar_personal=_p3.verificar_personal,
        verificar_equipo=_p3.verificar_equipo,
        buscar=_p3.buscar_incidentes,
        agente_timeout_s=float(os.getenv("AGENTE_TIMEOUT_S", "30")),
        riesgo_timeout_s=float(os.getenv("RIESGO_TIMEOUT_S", "45")),
    )


# -- puntos de entrada (los llama P1) -----------------------------------------------------------

async def ejecutar_run(run: Run, catalogo: Catalogo, emitir: Emitir, *, deps: Dependencias | None = None) -> Plan:
    deps = deps or dependencias_por_defecto()
    await emitir(TipoEvento.RUN_INICIADO, ACTOR_SISTEMA, {"tarea": run.tarea})

    evaluacion = await _evaluar_riesgo(run, catalogo, emitir, deps)
    controles = [c for cid in controles_exigidos(evaluacion) if (c := catalogo.control(cid))]
    resultados = await _verificar(run.tarea, controles, catalogo, emitir, deps,
                                  permitir_equivalencias=False, anunciar=True)
    return await _tras_consolidar(run, catalogo, emitir, deps, resultados)


async def confirmar_campo(
    run: Run, catalogo: Catalogo, conf: ConfirmacionesCampo, emitir: Emitir, *, deps: Dependencias | None = None,
) -> Plan:
    """Aplica las respuestas de campo al plan que las esperaba y recalcula (RF-F2-11)."""
    deps = deps or dependencias_por_defecto()
    con_alternativas = bool(run.planes_alternativos)
    base = run.planes_alternativos[0] if con_alternativas else run.plan
    if base is None:
        raise ValueError("El run no tiene un plan pendiente de confirmación de campo")

    respuestas = {r.requisito_id: r for r in conf.respuestas}
    resultados = [_aplicar_respuestas(rc, catalogo, respuestas, conf) for rc in base.resultados]
    estado = await _publicar_consolidado(resultados, emitir)

    if estado == EstadoSistema.BLOQUEADO and not con_alternativas:
        return await _tras_consolidar(run, catalogo, emitir, deps, resultados, ya_consolidado=True)
    if estado == EstadoSistema.BLOQUEADO:
        # La alternativa elegida falló en campo: no queda otra salida segura.
        original = (run.plan or base).model_copy(update={
            "escalamiento": _escalamiento(run, catalogo),
            "motivo": f"La alternativa propuesta no se cumplió en campo. {_motivo(resultados, catalogo)}",
        })
        return await _entregar(original, [], catalogo, emitir)

    actualizado = base.model_copy(update={"resultados": resultados, "estado_sistema": estado})
    if con_alternativas:
        return await _entregar(run.plan, [actualizado, *run.planes_alternativos[1:]], catalogo, emitir)
    return await _entregar(actualizado, [], catalogo, emitir)


# -- Riesgo ----------------------------------------------------------------------------------------

async def _evaluar_riesgo(run: Run, catalogo: Catalogo, emitir: Emitir, deps: Dependencias) -> EvaluacionRiesgo:
    try:
        return await asyncio.wait_for(
            evaluar_riesgo(run.tarea, catalogo, emitir, escenario_id=run.escenario_id,
                           buscar=deps.buscar, cliente=deps.cliente),
            deps.riesgo_timeout_s)
    except asyncio.TimeoutError:
        log.error("riesgo: tiempo límite agotado; se usa el checklist base del catálogo")
        evaluacion, _ = filtrar_y_completar(None, run.tarea, catalogo, set())
        await emitir(TipoEvento.AGENTE_COMPLETADO, ACTOR_RIESGO, {
            "agente": ACTOR_RIESGO, "evaluacion": evaluacion,
            "resumen": "Tiempo límite agotado; se aplicó el checklist base del catálogo."})
        return evaluacion


# -- verificación (Personal ‖ Equipo) -------------------------------------------------------------

async def _verificar(
    tarea, controles: list[Control], catalogo: Catalogo, emitir: Emitir, deps: Dependencias,
    *, permitir_equivalencias: bool, anunciar: bool,
) -> list[ResultadoControl]:
    """Reparte cada requisito exactamente una vez y consolida por control (RF-F1-11, RF-F1-12)."""
    personal: list[RequisitoAVerificar] = []
    equipo: list[RequisitoAVerificar] = []
    campo: list[ResultadoRequisito] = []
    for control in controles:
        for req in control.requisitos:
            pedido = RequisitoAVerificar(control_id=control.id, requisito=req)
            if req.tipo == TipoRequisito.COMPETENCIA:
                personal.append(pedido)
            elif req.tipo == TipoRequisito.EQUIPO:
                equipo.append(pedido)
            else:  # condicion_campo: ningún dato puede confirmarla en la primera pasada
                campo.append(ResultadoRequisito(
                    control_id=control.id, requisito_id=req.id, estado=EstadoControl.NO_VERIFICABLE,
                    verificado_por=ACTOR_SUPERVISOR, detalle="Requiere confirmación en campo"))

    def solicitud(actor: str, requisitos: list[RequisitoAVerificar]) -> AgenteSolicitud:
        return AgenteSolicitud(agente=actor, tarea=tarea, requisitos=requisitos,
                               permitir_equivalencias=permitir_equivalencias)

    res_personal, res_equipo = await asyncio.gather(
        _correr_agente(ACTOR_PERSONAL, deps.verificar_personal, solicitud(ACTOR_PERSONAL, personal),
                       catalogo, emitir, deps, anunciar),
        _correr_agente(ACTOR_EQUIPO, deps.verificar_equipo, solicitud(ACTOR_EQUIPO, equipo),
                       catalogo, emitir, deps, anunciar),
    )
    todos = [*res_personal, *res_equipo, *campo]
    return [consolidar_control(c, todos) for c in controles]


async def _correr_agente(
    actor: str, verificar: Verificador, sol: AgenteSolicitud, catalogo: Catalogo, emitir: Emitir,
    deps: Dependencias, anunciar: bool,
) -> list[ResultadoRequisito]:
    """Un fallo, un tiempo límite o una salida inválida dejan sus requisitos NO_VERIFICABLE (RF-F1-06)."""
    if anunciar:
        await emitir(TipoEvento.AGENTE_INICIADO, actor, {"agente": actor})
    try:
        resultados = await asyncio.wait_for(verificar(sol, catalogo, emitir), deps.agente_timeout_s) \
            if sol.requisitos else []
        pedidos = {(r.control_id, r.requisito.id) for r in sol.requisitos}
        resultados = [r for r in resultados if (r.control_id, r.requisito_id) in pedidos]
        resumen = _resumen(resultados)
    except Exception as e:
        log.warning("%s falló: %s: %s", actor, type(e).__name__, e)
        detalle = f"El agente no pudo verificar ({type(e).__name__})"
        resultados = [ResultadoRequisito(control_id=r.control_id, requisito_id=r.requisito.id,
                                         estado=EstadoControl.NO_VERIFICABLE, verificado_por=actor, detalle=detalle)
                      for r in sol.requisitos]
        resumen = detalle
    if anunciar:
        await emitir(TipoEvento.AGENTE_COMPLETADO, actor,
                     {"agente": actor, "resumen": resumen, "resultados": resultados})
    return resultados


def _resumen(resultados: list[ResultadoRequisito]) -> str:
    cuenta = {e: sum(r.estado == e for r in resultados) for e in EstadoControl}
    return f"{len(resultados)} requisito(s): " + ", ".join(f"{n} {e.value}" for e, n in cuenta.items() if n) \
        if resultados else "Sin requisitos para este agente."


# -- consolidación, conflicto y plan -------------------------------------------------------------------

async def _publicar_consolidado(resultados: list[ResultadoControl], emitir: Emitir) -> EstadoSistema:
    estado = calcular_estado_sistema(resultados)
    await emitir(TipoEvento.SUPERVISOR_CONSOLIDADO, ACTOR_SUPERVISOR,
                 {"resultados": resultados, "estado_sistema": estado})
    return estado


async def _tras_consolidar(
    run: Run, catalogo: Catalogo, emitir: Emitir, deps: Dependencias, resultados: list[ResultadoControl],
    *, ya_consolidado: bool = False,
) -> Plan:
    estado = calcular_estado_sistema(resultados) if ya_consolidado else await _publicar_consolidado(resultados, emitir)
    if estado == EstadoSistema.BLOQUEADO:
        return await _resolver_conflicto(run, catalogo, emitir, deps, resultados)
    plan = Plan(run_id=run.id, estado_sistema=estado, asignacion=run.tarea.asignacion, resultados=resultados,
                motivo=None if estado == EstadoSistema.RECOMENDADO else _motivo_sin_recomendar(resultados, catalogo))
    return await _entregar(plan, [], catalogo, emitir)


async def _resolver_conflicto(
    run: Run, catalogo: Catalogo, emitir: Emitir, deps: Dependencias, resultados: list[ResultadoControl],
) -> Plan:
    """Hasta 2 rondas: el LLM propone, las herramientas verifican (RF-F2-01..07, RT-06)."""
    tarea = run.tarea
    controles = [c for rc in resultados if (c := catalogo.control(rc.control_id))]
    detectados = _fallos(resultados, catalogo)
    for f in detectados:
        await emitir(TipoEvento.CONFLICTO_DETECTADO, ACTOR_SUPERVISOR, PayloadConflictoDetectado(
            control_id=f["control_id"], requisito_id=f["requisito_id"], causa=f["detalle"],
            evidencia=f["_evidencia"]))
    fallos = [{k: v for k, v in f.items() if k != "_evidencia"} for f in detectados]  # lo que ve el LLM

    verificadas: list[Plan] = []
    motivos_previos: list[str] = []
    vistas: set[str] = set()
    for ronda in (1, 2):
        alternativas, descartes = await proponer_alternativas(
            tarea, catalogo, fallos, ronda, motivos_previos, vistas,
            escenario_id=run.escenario_id, cliente=deps.cliente)
        motivos_previos += [f"ronda {ronda}: {d}" for d in descartes]
        if not alternativas:
            continue
        await emitir(TipoEvento.CONFLICTO_ALTERNATIVAS, ACTOR_SUPERVISOR,
                     PayloadConflictoAlternativas(ronda=ronda, alternativas=alternativas))
        for alt in alternativas:
            plan_alt = await _verificar_alternativa(alt, tarea, controles, catalogo, emitir, deps, run.id)
            if alt.cumple_bloqueantes:
                verificadas.append(plan_alt)
            else:
                motivos_previos.append(f"ronda {ronda}, {describir(alt.cambios)}: {alt.motivo_fallo}")
        if verificadas:
            break

    motivo = _motivo(resultados, catalogo)
    if verificadas:
        verificadas.sort(key=lambda p: (p.estado_sistema != EstadoSistema.RECOMENDADO, len(p.cambios)))
        original = Plan(run_id=run.id, estado_sistema=EstadoSistema.BLOQUEADO, asignacion=tarea.asignacion,
                        resultados=resultados, motivo=f"Plan original bloqueado. {motivo}")
        return await _entregar(original, verificadas, catalogo, emitir)
    original = Plan(run_id=run.id, estado_sistema=EstadoSistema.BLOQUEADO, asignacion=tarea.asignacion,
                    resultados=resultados, escalamiento=_escalamiento(run, catalogo),
                    motivo=f"{motivo} Sin alternativa segura tras 2 rondas.")
    return await _entregar(original, [], catalogo, emitir)


async def _verificar_alternativa(
    alt: Alternativa, tarea, controles: list[Control], catalogo: Catalogo, emitir: Emitir, deps: Dependencias,
    run_id: str,
) -> Plan:
    """El veredicto sale de las herramientas, con equivalencias permitidas; el LLM no interviene."""
    tarea_alt = aplicar_cambios(tarea, alt.cambios)
    resultados = await _verificar(tarea_alt, controles, catalogo, emitir, deps,
                                  permitir_equivalencias=True, anunciar=False)
    estado = calcular_estado_sistema(resultados)
    alt.cumple_bloqueantes = estado != EstadoSistema.BLOQUEADO
    alt.motivo_fallo = None if alt.cumple_bloqueantes else _motivo(resultados, catalogo)
    await emitir(TipoEvento.CONFLICTO_ALTERNATIVA_VERIFICADA, ACTOR_SUPERVISOR,
                 PayloadAlternativaVerificada(alternativa=alt))
    return Plan(id=alt.id, run_id=run_id, estado_sistema=estado, asignacion=tarea_alt.asignacion,
                cambios=alt.cambios, resultados=resultados,
                motivo=None if estado == EstadoSistema.RECOMENDADO else _motivo_sin_recomendar(resultados, catalogo))


async def _entregar(plan: Plan, alternativas: list[Plan], catalogo: Catalogo, emitir: Emitir) -> Plan:
    """Publica el plan y pide lo que sigue: campo, o decisión (solo rechazo si no se puede aprobar)."""
    await emitir(TipoEvento.PLAN_LISTO, ACTOR_SUPERVISOR,
                 PayloadPlanListo(plan=plan, planes_alternativos=alternativas))
    candidato = alternativas[0] if alternativas else plan
    if candidato.estado_sistema == EstadoSistema.RECOMENDADO:
        solo_rechazo = False
    else:
        preguntas = _preguntas(candidato, catalogo) if candidato.estado_sistema == EstadoSistema.REQUIERE_CAMPO else []
        if preguntas:
            await emitir(TipoEvento.HUMANO_CAMPO_REQUERIDO, ACTOR_SUPERVISOR, {"preguntas": preguntas})
            return candidato
        solo_rechazo = True
    await emitir(TipoEvento.HUMANO_DECISION_REQUERIDA, ACTOR_SUPERVISOR,
                 {"plan_id": candidato.id, "solo_rechazo": solo_rechazo})
    return candidato


# -- campo --------------------------------------------------------------------------------------------

def _es_campo(control: Control | None, requisito_id: str) -> bool:
    return bool(control) and any(r.id == requisito_id and r.tipo == TipoRequisito.CONDICION_CAMPO
                                 for r in control.requisitos)


def _aplicar_respuestas(rc: ResultadoControl, catalogo: Catalogo, respuestas: dict, conf: ConfirmacionesCampo) -> ResultadoControl:
    control = catalogo.control(rc.control_id)
    if control is None:
        return rc
    requisitos = []
    for rr in rc.requisitos:
        r = respuestas.get(rr.requisito_id)
        if r is not None and rr.estado == EstadoControl.NO_VERIFICABLE and _es_campo(control, rr.requisito_id):
            valor = ("sí" if r.cumple else "no") + (f": {r.nota}" if r.nota else "")
            rr = ResultadoRequisito(
                control_id=rr.control_id, requisito_id=rr.requisito_id,
                estado=EstadoControl.CUMPLE if r.cumple else EstadoControl.NO_CUMPLE,
                evidencia=[Evidencia(
                    registro=f"confirmacion_campo/{rr.requisito_id}", campo="respuesta", valor=valor,
                    fuente=Fuente(tipo=TipoFuente.SIMULADO,
                                  referencia=f"Confirmado por {conf.usuario} el {conf.ts:%Y-%m-%d %H:%M}"))],
                verificado_por=actor_humano(conf.usuario),
                detalle=r.nota or ("Confirmado en campo" if r.cumple else "No se cumple en campo"))
        requisitos.append(rr)
    return consolidar_control(control, requisitos)


def _preguntas(plan: Plan, catalogo: Catalogo) -> list[PreguntaCampo]:
    preguntas = []
    for rc in plan.resultados:
        control = catalogo.control(rc.control_id)
        for rr in rc.requisitos:
            if rr.estado == EstadoControl.NO_VERIFICABLE and _es_campo(control, rr.requisito_id):
                req = next(r for r in control.requisitos if r.id == rr.requisito_id)
                preguntas.append(PreguntaCampo(
                    requisito_id=req.id, control_id=rc.control_id,
                    pregunta=req.pregunta_campo or f"¿Se cumple: {req.descripcion}?"))
    return preguntas


# -- textos y datos para el conflicto ----------------------------------------------------------------

def _fallos(resultados: list[ResultadoControl], catalogo: Catalogo) -> list[dict[str, Any]]:
    """Requisitos NO_CUMPLE de controles bloqueantes, con los datos que necesita el LLM."""
    fallos = []
    for rc in resultados:
        control = catalogo.control(rc.control_id)
        if not (rc.bloqueante and rc.estado == EstadoControl.NO_CUMPLE) or control is None:
            continue
        for rr in rc.requisitos:
            req = next((r for r in control.requisitos if r.id == rr.requisito_id), None)
            if rr.estado != EstadoControl.NO_CUMPLE or req is None:
                continue
            fallos.append({
                "control_id": rc.control_id, "control": control.nombre, "requisito_id": req.id, "tipo": req.tipo.value,
                "descripcion": req.descripcion, "certificacion": req.certificacion,
                "certificaciones_equivalentes": req.certificaciones_equivalentes, "tipo_equipo": req.tipo_equipo,
                "detalle": rr.detalle or req.descripcion, "_evidencia": rr.evidencia,
            })
    return fallos


def _motivo(resultados: list[ResultadoControl], catalogo: Catalogo) -> str:
    partes = []
    for rc in resultados:
        if rc.bloqueante and rc.estado == EstadoControl.NO_CUMPLE:
            control = catalogo.control(rc.control_id)
            falla = next((r for r in rc.requisitos if r.estado == EstadoControl.NO_CUMPLE), None)
            partes.append(f"{control.nombre if control else rc.control_id}: {falla.detalle if falla else 'no cumple'}")
    return "; ".join(partes[:3]) + "." if partes else ""


def _motivo_sin_recomendar(resultados: list[ResultadoControl], catalogo: Catalogo) -> str:
    pendientes = [catalogo.control(rc.control_id).nombre if catalogo.control(rc.control_id) else rc.control_id
                  for rc in resultados if rc.estado == EstadoControl.NO_VERIFICABLE]
    if not resultados:
        return "No hay controles del catálogo para este tipo de tarea."
    return "Sin verificar: " + "; ".join(pendientes[:3]) + "." if pendientes else ""


def _escalamiento(run: Run, catalogo: Catalogo) -> str:
    escenario = catalogo.escenario(run.escenario_id) if run.escenario_id else None
    return (escenario.escalamiento if escenario and escenario.escalamiento else ESCALAMIENTO_GENERICO)
