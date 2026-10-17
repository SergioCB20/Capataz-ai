// Fuentes de eventos intercambiables: el reductor no sabe si los eventos vienen del SSE
// del backend o de un archivo de replay (RF-F1-35, RF-F3-03).
import type { Evento } from '@/api/types'

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
