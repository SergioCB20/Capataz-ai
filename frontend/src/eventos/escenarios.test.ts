// Escenarios E2, E2c y E3 con los fixtures escritos a mano (src/__fixtures__).
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Evento } from '@/api/types'
import e2 from '../__fixtures__/e2.json'
import e2c from '../__fixtures__/e2c.json'
import e3 from '../__fixtures__/e3.json'
import { estadoInicial, reducir, reducirTodos } from './reductor'
import { crearReplayLocal } from './replayLocal'

const E2 = e2 as unknown as Evento[]
const E2C = e2c as unknown as Evento[]
const E3 = e3 as unknown as Evento[]

describe('fixtures', () => {
  it.each([['e2', E2], ['e2c', E2C], ['e3', E3]])('%s tiene seq 1..n sin huecos', (_, ev) => {
    expect(ev.map((e) => e.seq)).toEqual(ev.map((_, i) => i + 1))
  })
})

describe('E2 conflicto (RF-F2-01..07, 21, 30)', () => {
  const s = reducirTodos(E2)
  it('detecta el conflicto y termina con plan RECOMENDADO esperando decisión', () => {
    expect(s.conflicto?.control_id).toBe('ctl-sostenimiento')
    expect(s.estadoRun).toBe('ESPERANDO_DECISION')
    expect(s.plan?.estado_sistema).toBe('RECOMENDADO')
  })
  it('muestra ≥ 2 alternativas y al menos una verificada; la fallida trae motivo', () => {
    expect(s.alternativas.length).toBeGreaterThanOrEqual(2)
    expect(s.alternativas.some((a) => a.cumple_bloqueantes === true)).toBe(true)
    const fallida = s.alternativas.find((a) => a.cumple_bloqueantes === false)
    expect(fallida?.motivo_fallo).toBeTruthy()
  })
  it('ofrece elegir entre planes verificados', () => {
    expect(s.planesAlternativos.map((p) => p.id)).toEqual(['plan-e2-alt-3'])
  })
  it('ningún agente queda trabajando al final', () => {
    for (const a of Object.values(s.agentes)) expect(a.estado).not.toBe('trabajando')
  })
})

describe('E3 bloqueo (RF-F2-07, 20, 33)', () => {
  const s = reducirTodos(E3)
  it('termina BLOQUEADO, solo rechazo, con escalamiento y 2 rondas', () => {
    expect(s.plan?.estado_sistema).toBe('BLOQUEADO')
    expect(s.decisionRequerida?.solo_rechazo).toBe(true)
    expect(s.plan?.escalamiento).toBeTruthy()
    expect(s.ronda).toBe(2)
    expect(s.alternativas.every((a) => a.cumple_bloqueantes === false)).toBe(true)
  })
})

describe('E2c campo (RF-F2-10, 11, 32)', () => {
  afterEach(() => vi.useRealTimers())

  function correr() {
    vi.useFakeTimers()
    let s = estadoInicial()
    const replay = crearReplayLocal(E2C, { velocidad: 10 })
    replay.fuente({ onEvento: (e) => (s = reducir(s, e)) })
    vi.runAllTimers()
    return { replay, estado: () => s }
  }

  it('se detiene esperando campo y, al confirmar «Sí», sigue hasta RECOMENDADO', () => {
    const { replay, estado } = correr()
    expect(estado().estadoRun).toBe('ESPERANDO_CAMPO')
    expect(estado().estadoSistema).toBe('REQUIERE_CAMPO')
    const sigue = replay.confirmarCampo({ usuario: 'supervisor', ts: 'x', respuestas: [{ requisito_id: 'req-ventilacion', cumple: true, nota: '' }] })
    vi.runAllTimers()
    expect(sigue).toBe(true)
    expect(estado().estadoRun).toBe('ESPERANDO_DECISION')
    expect(estado().estadoSistema).toBe('RECOMENDADO')
    expect(estado().resultadosRequisito['ctl-ventilacion/req-ventilacion'].estado).toBe('CUMPLE')
  })

  it('con «No» el replay sin backend no inventa el resultado: se detiene', () => {
    const { replay, estado } = correr()
    const sigue = replay.confirmarCampo({ usuario: 'supervisor', ts: 'x', respuestas: [{ requisito_id: 'req-ventilacion', cumple: false, nota: '' }] })
    vi.runAllTimers()
    expect(sigue).toBe(false)
    expect(estado().estadoSistema).toBe('REQUIERE_CAMPO')
    expect(estado().resultadosRequisito['ctl-ventilacion/req-ventilacion'].estado).toBe('NO_VERIFICABLE')
  })
})
