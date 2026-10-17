// Replay en el navegador sin backend (demo sin red y vitrina de Vercel; RF-F3-05, RF-F3-46).
// Reproduce el archivo y se PAUSA donde el archivo trae una acción humana
// (`humano.campo_confirmado`, `humano.decision_tomada`): esa acción la pone la persona en la UI.
// Las decisiones se simulan aquí y no se persisten.
import type { ConfirmacionesCampo, DecisionHumana, EstadoRun, Evento } from '@/api/types'
import { fuenteArchivo, type FuenteEventos, type ManejadoresFuente, type OpcionesArchivo } from './fuentes'

const esAccionHumana = (e: Evento) => e.tipo === 'humano.campo_confirmado' || e.tipo === 'humano.decision_tomada'

export interface ReplayLocal {
  fuente: FuenteEventos
  /** Devuelve false si el replay no puede seguir (respuesta «No»: no hay corrida grabada para ese caso). */
  confirmarCampo(c: ConfirmacionesCampo): boolean
  /** `soloRechazo` viene de `humano.decision_requerida`: un rechazo de plan bloqueado termina en BLOQUEADA. */
  decidir(d: DecisionHumana, soloRechazo: boolean): void
}

export function crearReplayLocal(eventos: Evento[], opciones: OpcionesArchivo = {}): ReplayLocal {
  const orden = [...eventos].sort((a, b) => a.seq - b.seq)
  const runId = orden[0]?.run_id ?? 'replay-local'
  let m: ManejadoresFuente | null = null
  let cursor = 0
  let ultimoSeq = 0
  let cerrarSegmento: (() => void) | undefined
  let terminado = false

  const emitir = (e: Evento) => {
    ultimoSeq = Math.max(ultimoSeq, e.seq)
    m?.onEvento(e)
  }

  const reproducirDesde = (i: number) => {
    let j = i
    while (j < orden.length && !esAccionHumana(orden[j])) j++
    cursor = j
    cerrarSegmento = fuenteArchivo(orden.slice(i, j), opciones)({
      onEvento: emitir,
      onConexion: (c) => {
        if (c === 'cerrada' && cursor >= orden.length) m?.onConexion?.('cerrada')
      },
    })
  }

  const siguienteSeq = (tipo: Evento['tipo']) => (orden[cursor]?.tipo === tipo ? orden[cursor].seq : ultimoSeq + 1)

  return {
    fuente: (manejadores) => {
      m = manejadores
      m.onConexion?.('abierta')
      reproducirDesde(0)
      return () => {
        terminado = true
        cerrarSegmento?.()
        m = null
      }
    },

    confirmarCampo(c) {
      if (terminado) return false
      const enArchivo = orden[cursor]?.tipo === 'humano.campo_confirmado'
      emitir({
        run_id: runId, seq: siguienteSeq('humano.campo_confirmado'), ts: new Date().toISOString(),
        tipo: 'humano.campo_confirmado', actor: `humano:${c.usuario}`, payload: { confirmaciones: c },
      })
      // El resto del archivo asume que todo se confirmó. Sin backend no se recalcula el estado
      // (esa lógica es del backend, RT-02), así que con algún «No» el replay se detiene.
      const todoSi = c.respuestas.every((r) => r.cumple)
      if (enArchivo && todoSi) {
        reproducirDesde(cursor + 1)
        return true
      }
      terminado = true
      m?.onConexion?.('cerrada')
      return false
    },

    decidir(d, soloRechazo) {
      if (terminado) return
      cerrarSegmento?.()
      const seq = siguienteSeq('humano.decision_tomada')
      const estado: EstadoRun = d.decision === 'aprobar' ? 'APROBADA' : soloRechazo ? 'BLOQUEADA' : 'RECHAZADA'
      const ts = new Date().toISOString()
      emitir({ run_id: runId, seq, ts, tipo: 'humano.decision_tomada', actor: `humano:${d.usuario}`, payload: { decision: d } })
      emitir({ run_id: runId, seq: seq + 1, ts, tipo: 'run.finalizado', actor: 'sistema', payload: { estado } })
      terminado = true
      m?.onConexion?.('cerrada')
    },
  }
}
