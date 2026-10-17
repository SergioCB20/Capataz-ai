// Tipos escritos a mano según los «Acuerdos de interfaz» de
// openspec/changes/p1-contrato-api-runtime/design.md.
// PROVISIONAL: cuando el backend exponga el OpenAPI, este archivo se reemplaza por el
// generado con openapi-typescript (RF-F0-03). No agregar lógica aquí.

export type EstadoControl = 'CUMPLE' | 'NO_VERIFICABLE' | 'NO_CUMPLE'
export type EstadoSistema = 'RECOMENDADO' | 'REQUIERE_CAMPO' | 'BLOQUEADO'
export type EstadoRun =
  | 'EVALUANDO'
  | 'RESOLVIENDO_CONFLICTO'
  | 'ESPERANDO_CAMPO'
  | 'ESPERANDO_DECISION'
  | 'APROBADA'
  | 'RECHAZADA'
  | 'BLOQUEADA'
  | 'ERROR'
export type TipoRequisito = 'competencia' | 'equipo' | 'condicion_campo'
export type EstadoEquipo = 'operativo' | 'mantenimiento' | 'fuera_servicio'
export type TipoFuente = 'normativa' | 'guia' | 'simulado'
export type TipoCambio = 'reprogramar_turno' | 'equipo_equivalente' | 'certificacion_equivalente'

export const ESTADOS_RUN_TERMINALES: readonly EstadoRun[] = ['APROBADA', 'RECHAZADA', 'BLOQUEADA', 'ERROR']

export interface Fuente {
  tipo: TipoFuente
  referencia: string
  url?: string | null
}

export interface TurnoRef {
  fecha: string // date ISO
  turno: 'dia' | 'noche'
}

export interface Requisito {
  id: string
  tipo: TipoRequisito
  descripcion: string
  certificacion?: string | null
  tipo_equipo?: string | null
  pregunta_campo?: string | null
  certificaciones_equivalentes?: string[]
}

export interface Control {
  id: string
  nombre: string
  peligro_id: string
  bloqueante: boolean
  aplica_a: string[]
  requisitos: Requisito[]
  fuente: Fuente
}

export interface Certificacion {
  codigo: string
  vence: string
}

export interface Persona {
  id: string
  nombre: string
  rol: string
  certificaciones: Certificacion[]
  turnos: TurnoRef[]
  fuente: Fuente
}

export interface Equipo {
  id: string
  nombre: string
  tipo_equipo: string
  estado: EstadoEquipo
  tipos_equivalentes: string[]
  /** Turnos en que el equipo NO está disponible. */
  mantenimiento?: TurnoRef[]
  fuente: Fuente
}

export interface Incidente {
  id: string
  fecha: string
  planta: string
  nivel_real: string
  nivel_potencial: string
  riesgo_critico: string
  descripcion: string
  equipo: string
  actividad: string
  tipo_tarea: string
  causa_raiz: string
  control_fallido: string
  fuente: Fuente
}

export interface Asignacion {
  personas: string[]
  equipos: string[]
}

export interface Tarea {
  id: string
  tipo_tarea: string
  descripcion: string
  zona: string
  turno: TurnoRef
  asignacion: Asignacion
}

export interface Escenario {
  id: string
  nombre: string
  tarea: Tarea
  resultado_esperado: EstadoSistema
  escalamiento: string | null
}

// Peligros y tipos de tarea no tienen campos fijados en los acuerdos: mínimo común.
export interface Peligro {
  id: string
  nombre?: string
  [k: string]: unknown
}
export interface TipoTarea {
  id: string
  nombre?: string
  [k: string]: unknown
}

export interface Catalogo {
  peligros: Peligro[]
  tipos_tarea: TipoTarea[]
  controles: Control[]
  personas: Persona[]
  equipos: Equipo[]
  incidentes: Incidente[]
  escenarios: Escenario[]
}

export interface PeligroDetectado {
  peligro_id: string
  justificacion: string
  controles: string[]
  incidentes_similares: string[]
}

export interface EvaluacionRiesgo {
  peligros: PeligroDetectado[]
}

export interface Evidencia {
  registro: string
  campo: string
  valor: string
  fuente: Fuente
}

export interface ResultadoRequisito {
  control_id: string
  requisito_id: string
  estado: EstadoControl
  evidencia: Evidencia[]
  verificado_por: string
  detalle: string
}

export interface ResultadoControl {
  control_id: string
  bloqueante: boolean
  estado: EstadoControl
  requisitos: ResultadoRequisito[]
}

export interface TraceHerramienta {
  nombre: string
  entrada: Record<string, unknown>
  salida_resumen: string
  duracion_ms: number
}

export interface Cambio {
  tipo: TipoCambio
  desde: string
  hacia: string
  motivo: string
}

export interface Alternativa {
  id: string
  ronda: 1 | 2
  cambios: Cambio[]
  explicacion: string
  cumple_bloqueantes: boolean | null
  motivo_fallo?: string | null
}

export interface Plan {
  id: string
  run_id: string
  estado_sistema: EstadoSistema
  asignacion: Asignacion
  cambios: Cambio[]
  resultados: ResultadoControl[]
  escalamiento?: string | null
  /** Por qué el plan quedó en su estado (P2: explica el bloqueo del plan original). */
  motivo?: string | null
}

export interface DecisionHumana {
  plan_id: string
  decision: 'aprobar' | 'rechazar'
  comentario?: string | null
  usuario: string
}

export interface RespuestaCampo {
  requisito_id: string
  cumple: boolean
  nota: string
}

export interface ConfirmacionesCampo {
  usuario: string
  ts: string
  respuestas: RespuestaCampo[]
}

export type ModoRun = 'vivo' | 'replay'

export interface RunCrear {
  modo: ModoRun
  escenario_id?: string | null
  tarea?: Tarea | null
}

export interface RunCreado {
  run_id: string
}

export interface Run {
  id: string
  estado: EstadoRun
  modo: ModoRun
  tarea: Tarea
  plan?: Plan | null
  decision?: DecisionHumana | null
}

// ---- Eventos ----

export type IdAgente = 'supervisor' | 'riesgo' | 'personal' | 'equipo'

export interface PayloadPorTipo {
  'run.iniciado': { tarea: Tarea }
  'agente.iniciado': { agente: string }
  'agente.herramienta': { agente: string; trace: TraceHerramienta }
  'agente.completado': {
    agente: string
    resumen: string
    resultados?: ResultadoRequisito[]
    evaluacion?: EvaluacionRiesgo
  }
  'supervisor.consolidado': { resultados: ResultadoControl[]; estado_sistema: EstadoSistema }
  'conflicto.detectado': { control_id: string; requisito_id: string; causa: string; evidencia: Evidencia[] }
  'conflicto.alternativas': { ronda: 1 | 2; alternativas: Alternativa[] }
  'conflicto.alternativa_verificada': { alternativa: Alternativa }
  'plan.listo': { plan: Plan; planes_alternativos?: Plan[] }
  'humano.campo_requerido': { preguntas: { requisito_id: string; pregunta: string }[] }
  'humano.campo_confirmado': { confirmaciones: ConfirmacionesCampo }
  'humano.decision_requerida': { plan_id: string; solo_rechazo: boolean }
  'humano.decision_tomada': { decision: DecisionHumana }
  'run.finalizado': { estado: EstadoRun }
  'run.error': { mensaje: string }
}

export type TipoEvento = keyof PayloadPorTipo

export type Evento = {
  [T in TipoEvento]: {
    run_id: string
    seq: number
    ts: string // datetime ISO
    tipo: T
    actor: string
    payload: PayloadPorTipo[T]
  }
}[TipoEvento]

export interface Health {
  store: string
  llm_mode: string
}
