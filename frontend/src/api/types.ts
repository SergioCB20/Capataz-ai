// Tipos del frontend a partir del contrato (RF-F0-03).
// Fuente: src/api/schema.d.ts, GENERADO desde el OpenAPI de FastAPI con `pnpm gen:types`.
// No editar schema.d.ts a mano: si el contrato cambia, regenerar y correr `pnpm typecheck`.
//
// Aquí solo se añaden: (1) `Salida<T>` para respuestas, porque el backend siempre envía los campos
// con valor por defecto aunque el OpenAPI los marque opcionales, y (2) los payloads de eventos
// por tipo, que el OpenAPI declara como diccionario genérico (`PAYLOAD_POR_TIPO` vive en contract.py).
import type { components } from './schema'

type S = components['schemas']

/** Respuesta del backend: todos los campos presentes (recursivo). */
export type Salida<T> = T extends (infer U)[]
  ? Salida<U>[]
  : T extends object
    ? { [K in keyof T]-?: Salida<T[K]> }
    : T

// ---- Enums (generados) ----
export type EstadoControl = S['EstadoControl']
export type EstadoSistema = S['EstadoSistema']
export type EstadoRun = S['EstadoRun']
export type TipoRequisito = S['TipoRequisito']
export type EstadoEquipo = S['EstadoEquipo']
export type TipoFuente = S['TipoFuente']
export type TipoCambio = S['TipoCambio']
export type TipoEvento = S['TipoEvento']
export type ModoRun = S['RunCrear']['modo']

export const ESTADOS_RUN_TERMINALES: readonly EstadoRun[] = ['APROBADA', 'RECHAZADA', 'BLOQUEADA', 'ERROR']

// ---- Modelos que llegan del backend (generados + Salida) ----
export type Fuente = Salida<S['Fuente']>
export type TurnoRef = Salida<S['TurnoRef']>
export type Requisito = Salida<S['Requisito']>
export type Control = Salida<S['Control']>
export type Certificacion = Salida<S['Certificacion']>
export type Persona = Salida<S['Persona']>
export type Equipo = Salida<S['Equipo']>
export type Incidente = Salida<S['Incidente']>
export type Asignacion = Salida<S['Asignacion']>
export type Tarea = Salida<S['Tarea']>
export type Escenario = Salida<S['Escenario']>
export type Peligro = Salida<S['Peligro']>
export type TipoTarea = Salida<S['TipoTarea']>
export type Catalogo = Salida<S['Catalogo']>
export type Evidencia = Salida<S['Evidencia']>
export type ResultadoRequisito = Salida<S['ResultadoRequisito']>
export type ResultadoControl = Salida<S['ResultadoControl']>
export type Cambio = Salida<S['Cambio']>
export type Plan = Salida<S['Plan']>
export type Run = Salida<S['Run']>
export type RunCreado = Salida<S['RunCreado']>

// ---- Lo que envía el frontend (entradas, tal cual el OpenAPI) ----
export type RunCrear = S['RunCrear']
export type DecisionHumana = Salida<S['DecisionHumana']>
export type RespuestaCampo = S['RespuestaCampo']
export type ConfirmacionesCampo = S['ConfirmacionesCampo']

// ---- Modelos que solo viajan dentro de eventos (no están en el OpenAPI) ----
// Según los acuerdos de interfaz de P1 (openspec/changes/p1-contrato-api-runtime/design.md).
export interface PeligroDetectado {
  peligro_id: string
  justificacion: string
  controles: string[]
  incidentes_similares: string[]
}

export interface EvaluacionRiesgo {
  peligros: PeligroDetectado[]
}

export interface TraceHerramienta {
  nombre: string
  entrada: Record<string, unknown>
  salida_resumen: string
  duracion_ms: number
}

export interface Alternativa {
  id: string
  ronda: 1 | 2
  cambios: Cambio[]
  explicacion: string
  cumple_bloqueantes: boolean | null
  motivo_fallo?: string | null
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
  'humano.campo_requerido': { preguntas: { requisito_id: string; pregunta: string; control_id?: string }[] }
  'humano.campo_confirmado': { confirmaciones: ConfirmacionesCampo }
  'humano.decision_requerida': { plan_id: string; solo_rechazo: boolean }
  'humano.decision_tomada': { decision: DecisionHumana }
  'run.finalizado': { estado: EstadoRun }
  'run.error': { mensaje: string }
}

// Falla la compilación si el backend agrega o quita un TipoEvento y aquí no se refleja.
type Igual<A, B> = [A] extends [B] ? ([B] extends [A] ? true : false) : false
const _tiposEventoAlDia: Igual<keyof PayloadPorTipo, TipoEvento> = true
void _tiposEventoAlDia

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

/** GET /api/health devuelve un dict sin modelo en el OpenAPI. */
export interface Health {
  store: string
  llm_mode: string
  orquestador?: string
}
