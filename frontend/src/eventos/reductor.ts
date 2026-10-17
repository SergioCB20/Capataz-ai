// Reductor único de eventos (RF-F1-35): toda la UI se deriva de aquí, en vivo y en replay.
// Es puro: mismo arreglo de eventos => mismo estado. Ignora eventos repetidos (seq <= ultimoSeq),
// así una reconexión del SSE que reenvía eventos no altera el resultado.
import type {
  Alternativa,
  DecisionHumana,
  Evento,
  EstadoRun,
  EstadoSistema,
  EvaluacionRiesgo,
  Evidencia,
  IdAgente,
  Plan,
  ResultadoControl,
  ResultadoRequisito,
  Tarea,
  TipoEvento,
  TraceHerramienta,
} from '@/api/types'

export type EstadoAgente = 'inactivo' | 'trabajando' | 'completado' | 'error'

export interface VistaAgente {
  estado: EstadoAgente
  herramientas: TraceHerramienta[]
  resumen: string | null
}

export interface EntradaLineaTiempo {
  seq: number
  ts: string
  tipo: TipoEvento
  actor: string
  texto: string
}

export interface EstadoUI {
  runId: string | null
  estadoRun: EstadoRun | null
  tarea: Tarea | null
  agentes: Record<IdAgente, VistaAgente>
  evaluacion: EvaluacionRiesgo | null
  /** Clave `${control_id}/${requisito_id}`; el último resultado gana. */
  resultadosRequisito: Record<string, ResultadoRequisito>
  resultadosControl: ResultadoControl[]
  estadoSistema: EstadoSistema | null
  conflicto: { control_id: string; requisito_id: string; causa: string; evidencia: Evidencia[] } | null
  ronda: 1 | 2 | null
  alternativas: Alternativa[]
  plan: Plan | null
  planesAlternativos: Plan[]
  preguntasCampo: { requisito_id: string; pregunta: string }[]
  decisionRequerida: { plan_id: string; solo_rechazo: boolean } | null
  decision: DecisionHumana | null
  error: string | null
  lineaTiempo: EntradaLineaTiempo[]
  ultimoSeq: number
}

const agenteVacio = (): VistaAgente => ({ estado: 'inactivo', herramientas: [], resumen: null })

export const estadoInicial = (): EstadoUI => ({
  runId: null,
  estadoRun: null,
  tarea: null,
  agentes: {
    supervisor: agenteVacio(),
    riesgo: agenteVacio(),
    personal: agenteVacio(),
    equipo: agenteVacio(),
  },
  evaluacion: null,
  resultadosRequisito: {},
  resultadosControl: [],
  estadoSistema: null,
  conflicto: null,
  ronda: null,
  alternativas: [],
  plan: null,
  planesAlternativos: [],
  preguntasCampo: [],
  decisionRequerida: null,
  decision: null,
  error: null,
  lineaTiempo: [],
  ultimoSeq: 0,
})

/** `capataz:agente-riesgo` | `riesgo` => `riesgo`. Devuelve null si no es uno de los 4 agentes. */
export function idAgente(nombre: string): IdAgente | null {
  const corto = nombre.replace(/^capataz:agente-/, '')
  return corto === 'supervisor' || corto === 'riesgo' || corto === 'personal' || corto === 'equipo' ? corto : null
}

export const claveRequisito = (r: { control_id: string; requisito_id: string }) => `${r.control_id}/${r.requisito_id}`

function conAgente(estado: EstadoUI, nombre: string, cambio: (a: VistaAgente) => VistaAgente): EstadoUI {
  const id = idAgente(nombre)
  if (!id) return estado
  return { ...estado, agentes: { ...estado.agentes, [id]: cambio(estado.agentes[id]) } }
}

function conAlternativa(lista: Alternativa[], alt: Alternativa): Alternativa[] {
  const i = lista.findIndex((a) => a.id === alt.id)
  if (i === -1) return [...lista, alt]
  const copia = lista.slice()
  copia[i] = alt
  return copia
}

/** Texto en español para la línea de tiempo; null = el evento no va en la línea de tiempo. */
export function describirEvento(e: Evento): string | null {
  switch (e.tipo) {
    case 'run.iniciado':
      return `Inicio de la evaluación: ${e.payload.tarea.descripcion}`
    case 'supervisor.consolidado':
      return `Controles consolidados: plan ${e.payload.estado_sistema}`
    case 'conflicto.detectado':
      return `Conflicto en ${e.payload.control_id}: ${e.payload.causa}`
    case 'conflicto.alternativas':
      return `Ronda ${e.payload.ronda}: ${e.payload.alternativas.length} alternativas propuestas`
    case 'conflicto.alternativa_verificada': {
      const a = e.payload.alternativa
      return a.cumple_bloqueantes
        ? `Alternativa ${a.id} verificada con herramientas`
        : `Alternativa ${a.id} falló la verificación${a.motivo_fallo ? `: ${a.motivo_fallo}` : ''}`
    }
    case 'plan.listo':
      return `Plan (PTW borrador) listo: ${e.payload.plan.estado_sistema}`
    case 'humano.campo_requerido':
      return `Se requiere confirmación en campo (${e.payload.preguntas.length} preguntas)`
    case 'humano.campo_confirmado':
      return `Campo confirmado por ${e.payload.confirmaciones.usuario}`
    case 'humano.decision_requerida':
      return e.payload.solo_rechazo ? 'Decisión requerida: solo se admite rechazo' : 'Decisión requerida'
    case 'humano.decision_tomada': {
      const d = e.payload.decision
      return d.decision === 'aprobar'
        ? `Plan aprobado por ${d.usuario}`
        : `Plan rechazado por ${d.usuario}: ${d.comentario ?? ''}`
    }
    case 'run.finalizado':
      return `Evaluación finalizada: ${e.payload.estado}`
    case 'run.error':
      return `Error: ${e.payload.mensaje}`
    default:
      return null
  }
}

function aplicar(estado: EstadoUI, e: Evento): EstadoUI {
  switch (e.tipo) {
    case 'run.iniciado':
      return {
        ...conAgente(estado, 'supervisor', (a) => ({ ...a, estado: 'trabajando' })),
        runId: e.run_id,
        tarea: e.payload.tarea,
        estadoRun: 'EVALUANDO',
      }
    case 'agente.iniciado':
      return conAgente(estado, e.payload.agente, (a) => ({ ...a, estado: 'trabajando' }))
    case 'agente.herramienta':
      return conAgente(estado, e.payload.agente, (a) => ({ ...a, herramientas: [...a.herramientas, e.payload.trace] }))
    case 'agente.completado': {
      const p = e.payload
      let s = conAgente(estado, p.agente, (a) => ({ ...a, estado: 'completado', resumen: p.resumen }))
      if (p.evaluacion) s = { ...s, evaluacion: p.evaluacion }
      if (p.resultados?.length) {
        const nuevos = { ...s.resultadosRequisito }
        for (const r of p.resultados) nuevos[claveRequisito(r)] = r
        s = { ...s, resultadosRequisito: nuevos }
      }
      return s
    }
    case 'supervisor.consolidado': {
      const nuevos = { ...estado.resultadosRequisito }
      for (const c of e.payload.resultados) for (const r of c.requisitos) nuevos[claveRequisito(r)] = r
      return {
        ...estado,
        resultadosControl: e.payload.resultados,
        resultadosRequisito: nuevos,
        estadoSistema: e.payload.estado_sistema,
      }
    }
    case 'conflicto.detectado':
      return {
        ...conAgente(estado, 'supervisor', (a) => ({ ...a, estado: 'trabajando' })),
        conflicto: e.payload,
        estadoRun: 'RESOLVIENDO_CONFLICTO',
      }
    case 'conflicto.alternativas':
      return {
        ...estado,
        ronda: e.payload.ronda,
        alternativas: e.payload.alternativas.reduce(conAlternativa, estado.alternativas),
      }
    case 'conflicto.alternativa_verificada':
      return { ...estado, alternativas: conAlternativa(estado.alternativas, e.payload.alternativa) }
    case 'plan.listo':
      return {
        ...conAgente(estado, 'supervisor', (a) => ({ ...a, estado: 'completado' })),
        plan: e.payload.plan,
        planesAlternativos: e.payload.planes_alternativos ?? [],
        estadoSistema: e.payload.plan.estado_sistema,
      }
    case 'humano.campo_requerido':
      return { ...estado, preguntasCampo: e.payload.preguntas, estadoRun: 'ESPERANDO_CAMPO' }
    case 'humano.campo_confirmado':
      return { ...estado, preguntasCampo: [], estadoRun: 'EVALUANDO' }
    case 'humano.decision_requerida':
      return { ...estado, decisionRequerida: e.payload, estadoRun: 'ESPERANDO_DECISION' }
    case 'humano.decision_tomada':
      return { ...estado, decision: e.payload.decision, decisionRequerida: null }
    case 'run.finalizado':
      return { ...estado, estadoRun: e.payload.estado }
    case 'run.error': {
      const agentes = { ...estado.agentes }
      for (const id of Object.keys(agentes) as IdAgente[]) {
        if (agentes[id].estado === 'trabajando') agentes[id] = { ...agentes[id], estado: 'error' }
      }
      return { ...estado, agentes, error: e.payload.mensaje, estadoRun: 'ERROR' }
    }
  }
}

export function reducir(estado: EstadoUI, e: Evento): EstadoUI {
  if (e.seq <= estado.ultimoSeq) return estado
  const s = aplicar(estado, e)
  const texto = describirEvento(e)
  return {
    ...s,
    ultimoSeq: e.seq,
    lineaTiempo: texto
      ? [...s.lineaTiempo, { seq: e.seq, ts: e.ts, tipo: e.tipo, actor: e.actor, texto }]
      : s.lineaTiempo,
  }
}

export const reducirTodos = (eventos: Evento[], inicial: EstadoUI = estadoInicial()) => eventos.reduce(reducir, inicial)
