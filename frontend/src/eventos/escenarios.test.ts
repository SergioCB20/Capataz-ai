// Escenarios E2, E2c y E3 con los fixtures escritos a mano (src/__fixtures__).
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Evento } from '@/api/types'
import e2 from '../__fixtures__/e2.json'
import e2c from '../__fixtures__/e2c.json'
import e3 from '../__fixtures__/e3.json'
import { candidatos, estadoInicial, reducir, reducirTodos, sinAlternativaSegura } from './reductor'
import { crearReplayLocal } from './replayLocal'

const E2 = e2 as unknown as Evento[]
const E2C = e2c as unknown as Evento[]
const E3 = e3 as unknown as Evento[]

describe('fixtures', () => {
  it.each([['e2', E2], ['e2c', E2C], ['e3', E3]])('%s tiene seq 1..n sin huecos', (_, ev) => {
    expect(ev.map((e) => e.seq)).toEqual(ev.map((_, i) => i + 1))
  })
})

describe('E2 conflicto (RF-F2-01..07, 21, 30) con la convención de P2', () => {
  const s = reducirTodos(E2)
  it('guarda un conflicto por requisito que falla', () => {
    expect(s.conflictos.map((c) => c.requisito_id)).toEqual(['req-operador-empernador', 'req-jumbo-operativo'])
  })
  it('plan = original BLOQUEADO; el estado mostrado es el del mejor candidato', () => {
    expect(s.plan?.estado_sistema).toBe('BLOQUEADO')
    expect(s.plan?.motivo).toBeTruthy()
    expect(s.estadoSistema).toBe('RECOMENDADO')
    expect(s.estadoRun).toBe('ESPERANDO_DECISION')
    expect(s.decisionRequerida?.plan_id).toBe('alt-1')
    expect(sinAlternativaSegura(s)).toBe(false)
  })
  it('Plan.id == Alternativa.id en los candidatos', () => {
    const ids = candidatos(s).map((p) => p.id)
    expect(ids).toEqual(['alt-1', 'alt-3'])
    for (const id of ids) expect(s.alternativas.find((a) => a.id === id)?.cumple_bloqueantes).toBe(true)
  })
  it('muestra ≥ 2 alternativas y al menos una verificada; la fallida trae motivo', () => {
    expect(s.alternativas.length).toBeGreaterThanOrEqual(2)
    expect(s.alternativas.some((a) => a.cumple_bloqueantes === true)).toBe(true)
    const fallida = s.alternativas.find((a) => a.cumple_bloqueantes === false)
    expect(fallida?.motivo_fallo).toBeTruthy()
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
    expect(sinAlternativaSegura(s)).toBe(true)
    expect(candidatos(s).map((p) => p.id)).toEqual(['plan-e3'])
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
    expect(estado().plan?.id).toBe('plan-e2c')
    const sigue = replay.confirmarCampo({ usuario: 'supervisor', ts: 'x', respuestas: [{ requisito_id: 'req-ventilacion', cumple: true, nota: '' }] })
    vi.runAllTimers()
    expect(sigue).toBe(true)
    expect(estado().estadoRun).toBe('ESPERANDO_DECISION')
    expect(estado().estadoSistema).toBe('RECOMENDADO')
    expect(estado().resultadosRequisito['ctl-ventilacion/req-ventilacion'].estado).toBe('CUMPLE')
    expect(estado().plan?.id).toBe('plan-e2c') // mismo Plan.id tras confirmar (P2)
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
