"""Contrato de datos de CAPATAZ: única fuente de verdad.

Los nombres siguen los acuerdos de interfaz de
`openspec/changes/p1-contrato-api-runtime/design.md`. Agregar campos opcionales
está permitido; renombrar o quitar exige avisar a todo el equipo.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any, Awaitable, Callable, Literal

from pydantic import BaseModel, Field, model_validator


def _nuevo_id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:8]}"


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EstadoControl(StrEnum):
    """Orden de gravedad creciente: gana el peor (RT-02)."""

    CUMPLE = "CUMPLE"
    NO_VERIFICABLE = "NO_VERIFICABLE"
    NO_CUMPLE = "NO_CUMPLE"


GRAVEDAD: dict[EstadoControl, int] = {
    EstadoControl.CUMPLE: 0,
    EstadoControl.NO_VERIFICABLE: 1,
    EstadoControl.NO_CUMPLE: 2,
}


class EstadoSistema(StrEnum):
    RECOMENDADO = "RECOMENDADO"
    REQUIERE_CAMPO = "REQUIERE_CAMPO"
    BLOQUEADO = "BLOQUEADO"


class EstadoRun(StrEnum):
    EVALUANDO = "EVALUANDO"
    RESOLVIENDO_CONFLICTO = "RESOLVIENDO_CONFLICTO"
    ESPERANDO_CAMPO = "ESPERANDO_CAMPO"
    ESPERANDO_DECISION = "ESPERANDO_DECISION"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"  # plan viable rechazado
    BLOQUEADA = "BLOQUEADA"  # plan BLOQUEADO rechazado (única salida)
    ERROR = "ERROR"


ESTADOS_TERMINALES = frozenset(
    {EstadoRun.APROBADA, EstadoRun.RECHAZADA, EstadoRun.BLOQUEADA, EstadoRun.ERROR}
)


class TipoRequisito(StrEnum):
    COMPETENCIA = "competencia"
    EQUIPO = "equipo"
    CONDICION_CAMPO = "condicion_campo"


class EstadoEquipo(StrEnum):
    OPERATIVO = "operativo"
    MANTENIMIENTO = "mantenimiento"
    FUERA_SERVICIO = "fuera_servicio"


class TipoFuente(StrEnum):
    NORMATIVA = "normativa"
    GUIA = "guia"
    SIMULADO = "simulado"


class TipoCambio(StrEnum):
    REPROGRAMAR_TURNO = "reprogramar_turno"
    EQUIPO_EQUIVALENTE = "equipo_equivalente"
    CERTIFICACION_EQUIVALENTE = "certificacion_equivalente"


class TipoEvento(StrEnum):
    RUN_INICIADO = "run.iniciado"
    AGENTE_INICIADO = "agente.iniciado"
    AGENTE_HERRAMIENTA = "agente.herramienta"
    AGENTE_COMPLETADO = "agente.completado"
    SUPERVISOR_CONSOLIDADO = "supervisor.consolidado"
    CONFLICTO_DETECTADO = "conflicto.detectado"
    CONFLICTO_ALTERNATIVAS = "conflicto.alternativas"
    CONFLICTO_ALTERNATIVA_VERIFICADA = "conflicto.alternativa_verificada"
    PLAN_LISTO = "plan.listo"
    HUMANO_CAMPO_REQUERIDO = "humano.campo_requerido"
    HUMANO_CAMPO_CONFIRMADO = "humano.campo_confirmado"
    HUMANO_DECISION_REQUERIDA = "humano.decision_requerida"
    HUMANO_DECISION_TOMADA = "humano.decision_tomada"
    RUN_FINALIZADO = "run.finalizado"
    RUN_ERROR = "run.error"


# Actores (RF-F1-02). Las personas usan `actor_humano(usuario)`.
ACTOR_SUPERVISOR = "capataz:agente-supervisor"
ACTOR_RIESGO = "capataz:agente-riesgo"
ACTOR_PERSONAL = "capataz:agente-personal"
ACTOR_EQUIPO = "capataz:agente-equipo"
ACTOR_SISTEMA = "sistema"


def actor_humano(usuario: str) -> str:
    return f"humano:{usuario}"


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------


class Fuente(BaseModel):
    tipo: TipoFuente = TipoFuente.SIMULADO
    referencia: str = "Dato simulado"
    url: str | None = None


class TurnoRef(BaseModel):
    fecha: date
    turno: Literal["dia", "noche"]


class Requisito(BaseModel):
    id: str
    tipo: TipoRequisito
    descripcion: str
    certificacion: str | None = None  # competencia: código de certificación
    certificaciones_equivalentes: list[str] = Field(default_factory=list)
    tipo_equipo: str | None = None  # equipo: tipo requerido
    pregunta_campo: str | None = None  # condicion_campo: pregunta al humano


class Peligro(BaseModel):
    id: str
    nombre: str
    descripcion: str = ""
    fuente: Fuente = Field(default_factory=Fuente)


class TipoTarea(BaseModel):
    id: str
    nombre: str
    descripcion: str = ""


class Control(BaseModel):
    id: str
    nombre: str
    peligro_id: str
    bloqueante: bool = True
    aplica_a: list[str] = Field(default_factory=list)  # IDs de tipo de tarea
    requisitos: list[Requisito] = Field(default_factory=list)
    fuente: Fuente = Field(default_factory=Fuente)


class Certificacion(BaseModel):
    codigo: str
    vence: date
    nombre: str | None = None


class Persona(BaseModel):
    id: str
    nombre: str
    rol: str = ""
    certificaciones: list[Certificacion] = Field(default_factory=list)
    turnos: list[TurnoRef] = Field(default_factory=list)  # turnos en que está disponible
    fuente: Fuente = Field(default_factory=Fuente)


class Equipo(BaseModel):
    id: str
    nombre: str
    tipo_equipo: str
    estado: EstadoEquipo = EstadoEquipo.OPERATIVO
    tipos_equivalentes: list[str] = Field(default_factory=list)
    mantenimiento: list[TurnoRef] = Field(default_factory=list)  # turnos no disponibles
    fuente: Fuente = Field(default_factory=Fuente)


class Incidente(BaseModel):
    """Incidente sintético; estructura inspirada en Kaggle (columnas POR VERIFICAR)."""

    id: str
    fecha: date
    planta: str = ""
    nivel_real: str = ""
    nivel_potencial: str = ""
    riesgo_critico: str = ""
    descripcion: str = ""
    equipo: str | None = None
    actividad: str = ""
    tipo_tarea: str | None = None
    causa_raiz: str = ""
    control_fallido: str | None = None  # ID de control del catálogo
    fuente: Fuente = Field(default_factory=Fuente)


class Asignacion(BaseModel):
    personas: list[str] = Field(default_factory=list)
    equipos: list[str] = Field(default_factory=list)


class Tarea(BaseModel):
    id: str = Field(default_factory=lambda: _nuevo_id("tarea"))
    tipo_tarea: str
    descripcion: str = ""
    zona: str = ""
    turno: TurnoRef
    asignacion: Asignacion = Field(default_factory=Asignacion)  # propuesta original


class Escenario(BaseModel):
    id: str
    nombre: str
    tarea: Tarea
    resultado_esperado: EstadoSistema
    escalamiento: str | None = None


class Catalogo(BaseModel):
    peligros: list[Peligro] = Field(default_factory=list)
    tipos_tarea: list[TipoTarea] = Field(default_factory=list)
    controles: list[Control] = Field(default_factory=list)
    personas: list[Persona] = Field(default_factory=list)
    equipos: list[Equipo] = Field(default_factory=list)
    incidentes: list[Incidente] = Field(default_factory=list)
    escenarios: list[Escenario] = Field(default_factory=list)

    def escenario(self, escenario_id: str) -> Escenario | None:
        return next((e for e in self.escenarios if e.id == escenario_id), None)

    def control(self, control_id: str) -> Control | None:
        return next((c for c in self.controles if c.id == control_id), None)


# ---------------------------------------------------------------------------
# Verificación
# ---------------------------------------------------------------------------


class PeligroDetectado(BaseModel):
    peligro_id: str
    justificacion: str = ""
    controles: list[str] = Field(default_factory=list)
    incidentes_similares: list[str] = Field(default_factory=list)


class EvaluacionRiesgo(BaseModel):
    peligros: list[PeligroDetectado] = Field(default_factory=list)


class RequisitoAVerificar(BaseModel):
    control_id: str
    requisito: Requisito


class AgenteSolicitud(BaseModel):
    agente: str
    tarea: Tarea
    requisitos: list[RequisitoAVerificar] = Field(default_factory=list)
    permitir_equivalencias: bool = False


class Evidencia(BaseModel):
    registro: str  # p. ej. "equipos/EQ-03"
    campo: str  # p. ej. "estado"
    valor: Any
    fuente: Fuente = Field(default_factory=Fuente)


class ResultadoRequisito(BaseModel):
    control_id: str
    requisito_id: str
    estado: EstadoControl
    evidencia: list[Evidencia] = Field(default_factory=list)
    verificado_por: str
    detalle: str = ""


class ResultadoControl(BaseModel):
    control_id: str
    bloqueante: bool
    estado: EstadoControl
    requisitos: list[ResultadoRequisito] = Field(default_factory=list)


class TraceHerramienta(BaseModel):
    nombre: str
    entrada: dict[str, Any] = Field(default_factory=dict)
    salida_resumen: str = ""
    duracion_ms: int = 0


# ---------------------------------------------------------------------------
# Plan, alternativas y decisión
# ---------------------------------------------------------------------------


class Cambio(BaseModel):
    tipo: TipoCambio
    desde: str
    hacia: str
    motivo: str = ""


class Alternativa(BaseModel):
    id: str = Field(default_factory=lambda: _nuevo_id("alt"))
    ronda: Literal[1, 2]  # máximo 2 rondas (RF-F2-04)
    cambios: list[Cambio] = Field(default_factory=list)
    explicacion: str = ""  # del LLM, separada del veredicto (RF-F2-08)
    cumple_bloqueantes: bool | None = None  # veredicto de las herramientas
    motivo_fallo: str | None = None


class Plan(BaseModel):
    id: str = Field(default_factory=lambda: _nuevo_id("plan"))
    run_id: str
    estado_sistema: EstadoSistema
    asignacion: Asignacion = Field(default_factory=Asignacion)
    cambios: list[Cambio] = Field(default_factory=list)
    resultados: list[ResultadoControl] = Field(default_factory=list)
    escalamiento: str | None = None
    motivo: str | None = None


class DecisionHumana(BaseModel):
    plan_id: str
    decision: Literal["aprobar", "rechazar"]
    comentario: str | None = None
    usuario: str = "supervisor"

    @model_validator(mode="after")
    def _rechazo_con_comentario(self) -> "DecisionHumana":
        if self.decision == "rechazar" and not (self.comentario or "").strip():
            raise ValueError("Rechazar exige un comentario no vacío")
        return self


class RespuestaCampo(BaseModel):
    requisito_id: str
    cumple: bool
    nota: str = ""


class ConfirmacionesCampo(BaseModel):
    usuario: str = "supervisor"
    ts: datetime = Field(default_factory=_ahora)
    respuestas: list[RespuestaCampo] = Field(default_factory=list)


class PreguntaCampo(BaseModel):
    requisito_id: str
    pregunta: str
    control_id: str | None = None


# ---------------------------------------------------------------------------
# Runs y eventos
# ---------------------------------------------------------------------------


class RunCrear(BaseModel):
    modo: Literal["vivo", "replay"] = "vivo"
    escenario_id: str | None = None
    tarea: Tarea | None = None

    @model_validator(mode="after")
    def _origen(self) -> "RunCrear":
        if self.modo == "replay" and not self.escenario_id:
            raise ValueError("El modo replay exige escenario_id")
        if self.modo == "vivo" and not (self.escenario_id or self.tarea):
            raise ValueError("Indica escenario_id o tarea")
        return self


class RunCreado(BaseModel):
    run_id: str


class Run(BaseModel):
    id: str = Field(default_factory=lambda: _nuevo_id("run"))
    estado: EstadoRun = EstadoRun.EVALUANDO
    modo: Literal["vivo", "replay"] = "vivo"
    escenario_id: str | None = None
    tarea: Tarea
    plan: Plan | None = None
    planes_alternativos: list[Plan] = Field(default_factory=list)
    decision: DecisionHumana | None = None
    creado_en: datetime = Field(default_factory=_ahora)
    actualizado_en: datetime = Field(default_factory=_ahora)


class Evento(BaseModel):
    run_id: str
    seq: int
    ts: datetime = Field(default_factory=_ahora)
    tipo: TipoEvento
    actor: str
    payload: dict[str, Any] = Field(default_factory=dict)


class CasoEvaluacion(BaseModel):
    id: str
    tarea: Tarea
    falla_inyectada: str | None = None  # None = caso limpio
    detectable_por: Literal["checklist", "incidentes"] | None = None
    resultado_esperado: EstadoSistema


# (tipo, actor, payload) -> Evento ya persistido. P1 la implementa; P2 y P3 la llaman.
Emitir = Callable[[TipoEvento, str, "dict[str, Any] | BaseModel"], Awaitable[Evento]]


# ---------------------------------------------------------------------------
# Payloads por tipo de evento
# ---------------------------------------------------------------------------


class PayloadRunIniciado(BaseModel):
    tarea: Tarea


class PayloadAgenteIniciado(BaseModel):
    agente: str


class PayloadAgenteHerramienta(BaseModel):
    agente: str
    trace: TraceHerramienta


class PayloadAgenteCompletado(BaseModel):
    agente: str
    resumen: str = ""
    resultados: list[ResultadoRequisito] | None = None
    evaluacion: EvaluacionRiesgo | None = None


class PayloadSupervisorConsolidado(BaseModel):
    resultados: list[ResultadoControl]
    estado_sistema: EstadoSistema


class PayloadConflictoDetectado(BaseModel):
    control_id: str
    requisito_id: str
    causa: str
    evidencia: list[Evidencia] = Field(default_factory=list)


class PayloadConflictoAlternativas(BaseModel):
    ronda: Literal[1, 2]
    alternativas: list[Alternativa]


class PayloadAlternativaVerificada(BaseModel):
    alternativa: Alternativa


class PayloadPlanListo(BaseModel):
    plan: Plan
    planes_alternativos: list[Plan] = Field(default_factory=list)


class PayloadCampoRequerido(BaseModel):
    preguntas: list[PreguntaCampo]


class PayloadCampoConfirmado(BaseModel):
    confirmaciones: ConfirmacionesCampo


class PayloadDecisionRequerida(BaseModel):
    plan_id: str
    solo_rechazo: bool = False


class PayloadDecisionTomada(BaseModel):
    decision: DecisionHumana


class PayloadRunFinalizado(BaseModel):
    estado: EstadoRun


class PayloadRunError(BaseModel):
    mensaje: str


PAYLOAD_POR_TIPO: dict[TipoEvento, type[BaseModel]] = {
    TipoEvento.RUN_INICIADO: PayloadRunIniciado,
    TipoEvento.AGENTE_INICIADO: PayloadAgenteIniciado,
    TipoEvento.AGENTE_HERRAMIENTA: PayloadAgenteHerramienta,
    TipoEvento.AGENTE_COMPLETADO: PayloadAgenteCompletado,
    TipoEvento.SUPERVISOR_CONSOLIDADO: PayloadSupervisorConsolidado,
    TipoEvento.CONFLICTO_DETECTADO: PayloadConflictoDetectado,
    TipoEvento.CONFLICTO_ALTERNATIVAS: PayloadConflictoAlternativas,
    TipoEvento.CONFLICTO_ALTERNATIVA_VERIFICADA: PayloadAlternativaVerificada,
    TipoEvento.PLAN_LISTO: PayloadPlanListo,
    TipoEvento.HUMANO_CAMPO_REQUERIDO: PayloadCampoRequerido,
    TipoEvento.HUMANO_CAMPO_CONFIRMADO: PayloadCampoConfirmado,
    TipoEvento.HUMANO_DECISION_REQUERIDA: PayloadDecisionRequerida,
    TipoEvento.HUMANO_DECISION_TOMADA: PayloadDecisionTomada,
    TipoEvento.RUN_FINALIZADO: PayloadRunFinalizado,
    TipoEvento.RUN_ERROR: PayloadRunError,
}


def validar_payload(evento: Evento) -> BaseModel:
    """Valida el payload según su tipo; lanza `pydantic.ValidationError` si no cumple."""
    return PAYLOAD_POR_TIPO[evento.tipo].model_validate(evento.payload)


# ---------------------------------------------------------------------------
# Consolidación (RT-02, RT-03): no reimplementar fuera de aquí
# ---------------------------------------------------------------------------


def peor_estado(estados: list[EstadoControl]) -> EstadoControl:
    if not estados:
        return EstadoControl.NO_VERIFICABLE
    return max(estados, key=GRAVEDAD.__getitem__)


def exigir_evidencia(resultado: ResultadoRequisito) -> ResultadoRequisito:
    """Un CUMPLE sin evidencia se degrada a NO_VERIFICABLE (RF-F1-16)."""
    if resultado.estado == EstadoControl.CUMPLE and not resultado.evidencia:
        return resultado.model_copy(
            update={
                "estado": EstadoControl.NO_VERIFICABLE,
                "detalle": (resultado.detalle + " | CUMPLE sin evidencia").strip(" |"),
            }
        )
    return resultado


def consolidar_control(
    control: Control, resultados: list[ResultadoRequisito]
) -> ResultadoControl:
    """Gana el peor estado; un requisito sin resultado cuenta como NO_VERIFICABLE."""
    por_requisito = {
        r.requisito_id: exigir_evidencia(r)
        for r in resultados
        if r.control_id == control.id
    }
    finales: list[ResultadoRequisito] = []
    for req in control.requisitos:
        finales.append(
            por_requisito.get(req.id)
            or ResultadoRequisito(
                control_id=control.id,
                requisito_id=req.id,
                estado=EstadoControl.NO_VERIFICABLE,
                verificado_por=ACTOR_SISTEMA,
                detalle="Sin resultado de verificación",
            )
        )
    return ResultadoControl(
        control_id=control.id,
        bloqueante=control.bloqueante,
        estado=peor_estado([r.estado for r in finales]),
        requisitos=finales,
    )


def calcular_estado_sistema(resultados: list[ResultadoControl]) -> EstadoSistema:
    """Bloqueante NO_CUMPLE ⇒ BLOQUEADO; algún NO_VERIFICABLE ⇒ REQUIERE_CAMPO.

    Sin controles evaluados no se puede recomendar nada: REQUIERE_CAMPO.
    """
    if not resultados:
        return EstadoSistema.REQUIERE_CAMPO
    if any(r.bloqueante and r.estado == EstadoControl.NO_CUMPLE for r in resultados):
        return EstadoSistema.BLOQUEADO
    if any(r.estado == EstadoControl.NO_VERIFICABLE for r in resultados):
        return EstadoSistema.REQUIERE_CAMPO
    return EstadoSistema.RECOMENDADO
