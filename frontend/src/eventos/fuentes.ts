// Fuentes de eventos intercambiables: el reductor no sabe si los eventos vienen del SSE
// del backend o de un archivo de replay (RF-F1-35, RF-F3-03).
import { api } from '@/api/cliente'
import type { Evento, TipoEvento } from '@/api/types'

export type EstadoConexion = 'conectando' | 'abierta' | 'reconectando' | 'cerrada' | 'error'

export interface ManejadoresFuente {
  onEvento(e: Evento): void
  onConexion?(estado: EstadoConexion): void
}

/** Arranca la fuente y devuelve la función para cerrarla. */
export type FuenteEventos = (m: ManejadoresFuente) => () => void

export interface OpcionesArchivo {
  /** 1 = tiempos reales grabados; 2 = el doble de rápido. */
  velocidad?: number
  /** Tope de espera entre dos eventos (ms reales), para que el replay no se haga largo. */
  esperaMaxima?: number
}

/** Reproduce un arreglo de eventos respetando sus tiempos relativos (`ts`). */
export function fuenteArchivo(eventos: Evento[], opciones: OpcionesArchivo = {}): FuenteEventos {
  const velocidad = opciones.velocidad ?? 1
  const esperaMaxima = opciones.esperaMaxima ?? 2500
  const ordenados = [...eventos].sort((a, b) => a.seq - b.seq)

  return ({ onEvento, onConexion }) => {
    let cancelado = false
    let temporizador: ReturnType<typeof setTimeout> | undefined
    onConexion?.('abierta')

    const emitir = (i: number) => {
      if (cancelado) return
      if (i >= ordenados.length) {
        onConexion?.('cerrada')
        return
      }
      onEvento(ordenados[i])
      const siguiente = ordenados[i + 1]
      if (!siguiente) return emitir(i + 1)
      const delta = Date.parse(siguiente.ts) - Date.parse(ordenados[i].ts)
      const espera = Math.min(Math.max(delta, 0) / velocidad, esperaMaxima)
      temporizador = setTimeout(() => emitir(i + 1), espera)
    }

    temporizador = setTimeout(() => emitir(0), 0)
    return () => {
      cancelado = true
      clearTimeout(temporizador)
    }
  }
}

const TIPOS_EVENTO: TipoEvento[] = [
  'run.iniciado', 'agente.iniciado', 'agente.herramienta', 'agente.completado', 'supervisor.consolidado',
  'conflicto.detectado', 'conflicto.alternativas', 'conflicto.alternativa_verificada', 'plan.listo',
  'humano.campo_requerido', 'humano.campo_confirmado', 'humano.decision_requerida', 'humano.decision_tomada',
  'run.finalizado', 'run.error',
]
const FINALES: TipoEvento[] = ['run.finalizado', 'run.error']

/**
 * SSE del backend (RF-F1-03, RF-F1-36). El navegador reconecta solo y manda `Last-Event-ID`;
 * si la conexión queda cerrada, se reabre a mano pidiendo `?desde=` último seq visto.
 * Se cierra al recibir `run.finalizado` o `run.error`. El reductor descarta eventos repetidos.
 */
export function fuenteSSE(runId: string, opciones: { reintentoMs?: number } = {}): FuenteEventos {
  const reintentoMs = opciones.reintentoMs ?? 1500
  return ({ onEvento, onConexion }) => {
    let es: EventSource | null = null
    let ultimoSeq = 0
    let terminado = false
    let temporizador: ReturnType<typeof setTimeout> | undefined

    const recibir = (msg: MessageEvent<string>) => {
      let e: Evento
      try {
        e = JSON.parse(msg.data) as Evento
      } catch {
        return // latido u otro mensaje que no es un Evento
      }
      if (!e || typeof e.seq !== 'number') return
      ultimoSeq = Math.max(ultimoSeq, e.seq)
      onEvento(e)
      if (FINALES.includes(e.tipo)) {
        terminado = true
        es?.close()
        onConexion?.('cerrada')
      }
    }

    const abrir = () => {
      onConexion?.(ultimoSeq ? 'reconectando' : 'conectando')
      es = new EventSource(api.urlEventos(runId, ultimoSeq))
      es.onopen = () => onConexion?.('abierta')
      es.onmessage = recibir
      // El backend puede mandar `event: <tipo>`; escuchamos ambos formatos.
      for (const t of TIPOS_EVENTO) es.addEventListener(t, recibir as EventListener)
      es.onerror = () => {
        if (terminado) return
        if (es?.readyState === EventSource.CLOSED) {
          onConexion?.('reconectando')
          temporizador = setTimeout(abrir, reintentoMs)
        } else {
          onConexion?.('reconectando') // el navegador reintenta solo
        }
      }
    }

    abrir()
    return () => {
      terminado = true
      clearTimeout(temporizador)
      es?.close()
    }
  }
}
