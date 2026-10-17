import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Evento } from '@/api/types'
import e1 from '../../../replays/e1.json'
import { estadoInicial, reducir } from './reductor'
import { crearReplayLocal } from './replayLocal'

const eventosE1 = e1 as unknown as Evento[]

describe('crearReplayLocal', () => {
  afterEach(() => vi.useRealTimers())

  function correr(eventos: Evento[]) {
    vi.useFakeTimers()
    let s = estadoInicial()
    const replay = crearReplayLocal(eventos, { velocidad: 10 })
    replay.fuente({ onEvento: (e) => (s = reducir(s, e)) })
    vi.runAllTimers()
    return { replay, estado: () => s }
  }

  it('aprobar E1 termina el run en APROBADA', () => {
    const { replay, estado } = correr(eventosE1)
    expect(estado().estadoRun).toBe('ESPERANDO_DECISION')
    replay.decidir({ plan_id: 'plan-e1', decision: 'aprobar', usuario: 'supervisor' }, false)
    expect(estado().estadoRun).toBe('APROBADA')
    expect(estado().decision?.decision).toBe('aprobar')
    expect(estado().ultimoSeq).toBe(16)
  })

  it('rechazar un plan bloqueado termina en BLOQUEADA', () => {
    const { replay, estado } = correr(eventosE1)
    replay.decidir({ plan_id: 'plan-e1', decision: 'rechazar', comentario: 'sin alternativa', usuario: 'supervisor' }, true)
    expect(estado().estadoRun).toBe('BLOQUEADA')
  })

  it('se pausa en la acción humana grabada y reemplaza sus datos por los de la persona', () => {
    const grabados: Evento[] = [
      ...eventosE1,
      { run_id: 'replay-e1', seq: 15, ts: '2026-10-17T15:00:09.000Z', tipo: 'humano.decision_tomada', actor: 'humano:x',
        payload: { decision: { plan_id: 'plan-e1', decision: 'rechazar', comentario: 'grabado', usuario: 'x' } } },
      { run_id: 'replay-e1', seq: 16, ts: '2026-10-17T15:00:09.100Z', tipo: 'run.finalizado', actor: 'sistema',
        payload: { estado: 'RECHAZADA' } },
    ]
    const { replay, estado } = correr(grabados)
    expect(estado().ultimoSeq).toBe(14) // se detuvo antes de la decisión grabada
    replay.decidir({ plan_id: 'plan-e1', decision: 'aprobar', usuario: 'supervisor' }, false)
    expect(estado().estadoRun).toBe('APROBADA')
    expect(estado().decision?.usuario).toBe('supervisor')
  })
})
