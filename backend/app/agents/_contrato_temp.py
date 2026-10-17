"""TEMPORAL: modelos del contrato según «Acuerdos de interfaz» de p1-contrato-api-runtime/design.md.

Existe solo para que P2 avance antes de que P1 suba `app/contract.py`. Cuando ese archivo
esté en `main`, `agents/_contrato.py` lo usa en su lugar y este archivo se borra.
Los campos no listados en los acuerdos (Peligro, TipoTarea) siguen el contrato original.
"""
from datetime import date, datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field


class EstadoControl(str, Enum):
    CUMPLE = "CUMPLE"
    NO_VERIFICABLE = "NO_VERIFICABLE"
    NO_CUMPLE = "NO_CUMPLE"


class EstadoSistema(str, Enum):
    RECOMENDADO = "RECOMENDADO"
    REQUIERE_CAMPO = "REQUIERE_CAMPO"
    BLOQUEADO = "BLOQUEADO"


class TipoRequisito(str, Enum):
    COMPETENCIA = "competencia"
    EQUIPO = "equipo"
    CONDICION_CAMPO = "condicion_campo"


class EstadoEquipo(str, Enum):
    OPERATIVO = "operativo"
    MANTENIMIENTO = "mantenimiento"
    FUERA_SERVICIO = "fuera_servicio"


class TipoFuente(str, Enum):
    NORMATIVA = "normativa"
    GUIA = "guia"
    SIMULADO = "simulado"


class Fuente(BaseModel):
    tipo: TipoFuente
    referencia: str
    url: str | None = None


class TurnoRef(BaseModel):
    model_config = ConfigDict(frozen=True)
    fecha: date
    turno: Literal["dia", "noche"]


class Requisito(BaseModel):
    id: str
    tipo: TipoRequisito
    descripcion: str
    certificacion: str | None = None
    tipo_equipo: str | None = None
    pregunta_campo: str | None = None


class Control(BaseModel):
    id: str
    nombre: str
    peligro_id: str
    bloqueante: bool = True
    aplica_a: list[str]
    requisitos: list[Requisito]
    fuente: Fuente


class Certificacion(BaseModel):
    codigo: str
    vence: date


class Persona(BaseModel):
    id: str
    nombre: str
    rol: str
    certificaciones: list[Certificacion] = Field(default_factory=list)
    turnos: list[TurnoRef] = Field(default_factory=list)
    fuente: Fuente


class Equipo(BaseModel):
    id: str
    nombre: str
    tipo_equipo: str
    estado: EstadoEquipo = EstadoEquipo.OPERATIVO
    tipos_equivalentes: list[str] = Field(default_factory=list)
    fuente: Fuente


class Incidente(BaseModel):
    id: str
    fecha: date | None = None
    planta: str | None = None
    nivel_real: str | None = None
    nivel_potencial: str | None = None
    riesgo_critico: str | None = None
    descripcion: str = ""
    equipo: str | None = None
    actividad: str | None = None
    tipo_tarea: str | None = None
    causa_raiz: str | None = None
    control_fallido: str | None = None
    fuente: Fuente | None = None


class Asignacion(BaseModel):
    personas: list[str] = Field(default_factory=list)
    equipos: list[str] = Field(default_factory=list)


class Tarea(BaseModel):
    id: str
    tipo_tarea: str
    descripcion: str
    zona: str
    turno: TurnoRef
    asignacion: Asignacion = Field(default_factory=Asignacion)


class Peligro(BaseModel):
    id: str
    nombre: str
    categoria: str


class TipoTarea(BaseModel):
    id: str
    nombre: str
    descripcion: str = ""
    peligros: list[str]


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


class PeligroDetectado(BaseModel):
    peligro_id: str
    justificacion: str
    controles: list[str] = Field(default_factory=list)
    incidentes_similares: list[str] = Field(default_factory=list)


class EvaluacionRiesgo(BaseModel):
    peligros: list[PeligroDetectado]


class RequisitoAVerificar(BaseModel):
    control_id: str
    requisito: Requisito


class AgenteSolicitud(BaseModel):
    agente: str
    tarea: Tarea
    requisitos: list[RequisitoAVerificar]
    permitir_equivalencias: bool = False


class Evidencia(BaseModel):
    registro: str
    campo: str
    valor: str
    fuente: Fuente


class ResultadoRequisito(BaseModel):
    control_id: str
    requisito_id: str
    estado: EstadoControl
    evidencia: list[Evidencia] = Field(default_factory=list)
    verificado_por: str
    detalle: str = ""


class TraceHerramienta(BaseModel):
    nombre: str
    entrada: dict[str, Any] = Field(default_factory=dict)
    salida_resumen: str = ""
    duracion_ms: int = 0


class TipoEvento(str, Enum):
    RUN_INICIADO = "run.iniciado"
    AGENTE_INICIADO = "agente.iniciado"
    AGENTE_HERRAMIENTA = "agente.herramienta"
    AGENTE_COMPLETADO = "agente.completado"
    CONSOLIDADO = "supervisor.consolidado"
    CONFLICTO_DETECTADO = "conflicto.detectado"
    ALTERNATIVAS_GENERADAS = "conflicto.alternativas"
    ALTERNATIVA_VERIFICADA = "conflicto.alternativa_verificada"
    CAMPO_REQUERIDO = "humano.campo_requerido"
    CAMPO_CONFIRMADO = "humano.campo_confirmado"
    PLAN_LISTO = "plan.listo"
    DECISION_REQUERIDA = "humano.decision_requerida"
    DECISION_TOMADA = "humano.decision_tomada"
    RUN_FINALIZADO = "run.finalizado"
    RUN_ERROR = "run.error"


class Evento(BaseModel):
    run_id: str
    seq: int
    ts: datetime
    tipo: TipoEvento
    actor: str
    payload: dict[str, Any] = Field(default_factory=dict)


Emitir = Callable[[TipoEvento, str, dict[str, Any]], Awaitable[Evento]]
