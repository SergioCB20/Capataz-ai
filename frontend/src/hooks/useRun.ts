// Une fuente de eventos + reductor y expone las acciones humanas.
// Origen «backend»: POST /api/runs + SSE. Origen «local»: replay del archivo en el navegador.
import { useCallback, useEffect, useRef, useState } from 'react'
import { api, mensajeError } from '@/api/cliente'
import type { ConfirmacionesCampo, DecisionHumana, Evento, ModoRun, Tarea } from '@/api/types'
import { fuenteSSE, type EstadoConexion, type FuenteEventos } from '@/eventos/fuentes'
import { estadoInicial, reducir, type EstadoUI } from '@/eventos/reductor'
import { crearReplayLocal, type ReplayLocal } from '@/eventos/replayLocal'
import { replayLocal } from '@/replays'

export type OrigenRun = 'backend' | 'local'

export interface PeticionRun {
  modo: ModoRun
  escenarioId: string | null
  tarea: Tarea
}

export interface SesionRun {
  modo: ModoRun
  origen: OrigenRun
  runId: string
}

export const USUARIO = 'supervisor'

export function useRun() {
  const [estado, setEstado] = useState<EstadoUI>(estadoInicial)
  /** Eventos crudos (sin repetidos) para exportar la auditoría (RF-F3-30). */
  const [eventos, setEventos] = useState<Evento[]>([])
  const [sesion, setSesion] = useState<SesionRun | null>(null)
  const [conexion, setConexion] = useState<EstadoConexion>('cerrada')
  const [iniciando, setIniciando] = useState(false)
  const [errorInicio, setErrorInicio] = useState<string | null>(null)
  const [errorAccion, setErrorAccion] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  const cerrarRef = useRef<(() => void) | null>(null)
  const replayRef = useRef<ReplayLocal | null>(null)

  const detener = useCallback(() => {
    cerrarRef.current?.()
    cerrarRef.current = null
    replayRef.current = null
  }, [])

  useEffect(() => detener, [detener])

  const conectar = (fuente: FuenteEventos) => {
    cerrarRef.current = fuente({
      onEvento: (e) => {
        setEstado((s) => reducir(s, e))
        setEventos((lista) => (e.seq > (lista.at(-1)?.seq ?? 0) ? [...lista, e] : lista))
      },
      onConexion: setConexion,
    })
  }

  const iniciar = useCallback(
    async ({ modo, escenarioId, tarea }: PeticionRun) => {
      detener()
      setEstado(estadoInicial())
      setEventos([])
      setErrorInicio(null)
      setErrorAccion(null)
      setIniciando(true)
      try {
        const backendVivo = await api.health().then(() => true, () => false)

        const local = modo === 'replay' && escenarioId ? replayLocal(escenarioId) : null
        if (backendVivo) {
          try {
            const { run_id } = await api.crearRun({ modo, escenario_id: escenarioId, tarea: modo === 'vivo' ? tarea : null })
            setSesion({ modo, origen: 'backend', runId: run_id })
            conectar(fuenteSSE(run_id))
            return
          } catch (e) {
            // Replay que el backend no tiene grabado: se reproduce el local del navegador.
            if (!local) throw e
          }
        }

        if (modo === 'vivo') throw new Error('El servidor no responde. Usa el modo replay o arranca el backend (uvicorn en :8000).')
        const eventos = local
        if (!eventos) throw new Error(`No hay replay local para ${escenarioId ?? 'una tarea libre'}.`)
        const replay = crearReplayLocal(eventos, { velocidad: 1.5 })
        replayRef.current = replay
        setSesion({ modo, origen: 'local', runId: eventos[0]?.run_id ?? 'replay-local' })
        conectar(replay.fuente)
      } catch (e) {
        setSesion(null)
        setErrorInicio(mensajeError(e))
      } finally {
        setIniciando(false)
      }
    },
    [detener],
  )

  const decidir = useCallback(
    async (decision: 'aprobar' | 'rechazar', comentario?: string, planId?: string) => {
      const requerida = estado.decisionRequerida
      if (!sesion || !requerida) return
      // Con varias alternativas verificadas la persona elige el plan_id (RF-F2-21).
      const d: DecisionHumana = { plan_id: planId ?? requerida.plan_id, decision, comentario: comentario || null, usuario: USUARIO }
      setErrorAccion(null)
      if (sesion.origen === 'local') return replayRef.current?.decidir(d, requerida.solo_rechazo)
      setEnviando(true)
      try {
        await api.decidir(sesion.runId, d)
      } catch (e) {
        setErrorAccion(mensajeError(e))
      } finally {
        setEnviando(false)
      }
    },
    [estado.decisionRequerida, sesion],
  )

  const confirmarCampo = useCallback(
    async (respuestas: ConfirmacionesCampo['respuestas']) => {
      if (!sesion) return
      const c: ConfirmacionesCampo = { usuario: USUARIO, ts: new Date().toISOString(), respuestas }
      setErrorAccion(null)
      if (sesion.origen === 'local') {
        const sigue = replayRef.current?.confirmarCampo(c)
        if (!sigue) {
          setErrorAccion('Respuesta registrada. En el replay sin servidor solo hay corrida grabada para «Sí»; para ver el recálculo con «No», usa el modo en vivo.')
        }
        return
      }
      setEnviando(true)
      try {
        await api.confirmarCampo(sesion.runId, c)
      } catch (e) {
        setErrorAccion(mensajeError(e))
      } finally {
        setEnviando(false)
      }
    },
    [sesion],
  )

  const salir = useCallback(() => {
    detener()
    setSesion(null)
    setEstado(estadoInicial())
    setEventos([])
    setConexion('cerrada')
    setErrorAccion(null)
  }, [detener])

  return { estado, eventos, sesion, conexion, iniciando, errorInicio, errorAccion, enviando, iniciar, decidir, confirmarCampo, salir }
}

export type ControlRun = ReturnType<typeof useRun>
