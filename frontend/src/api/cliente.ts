// Cliente HTTP del backend (API de los acuerdos de interfaz de P1).
// VITE_API_URL vacío => mismo origen (en `pnpm dev` el proxy /api -> :8000). RF-F0-18.
import type { Catalogo, ConfirmacionesCampo, DecisionHumana, Health, Run, RunCrear, RunCreado } from './types'

export const BASE_API = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

export class ErrorApi extends Error {
  readonly status: number
  constructor(status: number, mensaje: string) {
    super(mensaje)
    this.status = status
  }
}

async function pedir<T>(ruta: string, init?: RequestInit & { tiempoMs?: number }): Promise<T> {
  const { tiempoMs = 10_000, ...resto } = init ?? {}
  let resp: Response
  try {
    resp = await fetch(`${BASE_API}${ruta}`, {
      ...resto,
      headers: { 'Content-Type': 'application/json', ...resto.headers },
      signal: AbortSignal.timeout(tiempoMs),
    })
  } catch {
    throw new ErrorApi(0, 'No se pudo conectar con el servidor.')
  }
  if (!resp.ok) {
    let detalle = resp.statusText
    try {
      const cuerpo = await resp.json()
      detalle = typeof cuerpo.detail === 'string' ? cuerpo.detail : JSON.stringify(cuerpo.detail ?? cuerpo)
    } catch {
      /* cuerpo no JSON */
    }
    throw new ErrorApi(resp.status, detalle)
  }
  return (await resp.json()) as T
}

const post = <T>(ruta: string, cuerpo: unknown) => pedir<T>(ruta, { method: 'POST', body: JSON.stringify(cuerpo) })

export const api = {
  health: () => pedir<Health>('/api/health', { tiempoMs: 1500 }),
  catalogo: () => pedir<Catalogo>('/api/catalogo'),
  crearRun: (datos: RunCrear) => post<RunCreado>('/api/runs', datos),
  leerRun: (id: string) => pedir<Run>(`/api/runs/${encodeURIComponent(id)}`),
  decidir: (id: string, d: DecisionHumana) => post<Run>(`/api/runs/${encodeURIComponent(id)}/decision`, d),
  confirmarCampo: (id: string, c: ConfirmacionesCampo) => post<Run>(`/api/runs/${encodeURIComponent(id)}/campo`, c),
  urlEventos: (id: string, desdeSeq = 0) =>
    `${BASE_API}/api/runs/${encodeURIComponent(id)}/eventos${desdeSeq ? `?desde=${desdeSeq}` : ''}`,
}

/** Mensaje en español para mostrar en la UI. */
export function mensajeError(e: unknown): string {
  if (e instanceof ErrorApi) {
    if (e.status === 0) return e.message
    if (e.status === 409) return `Operación no permitida en el estado actual del run (${e.message}).`
    if (e.status === 422) return `Datos inválidos: ${e.message}`
    return `Error del servidor (${e.status}): ${e.message}`
  }
  return e instanceof Error ? e.message : String(e)
}
