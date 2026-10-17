import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Evento } from '@/api/types'
import e1 from '../../../replays/e1.json'
import { estadoInicial, idAgente, reducir, reducirTodos } from './reductor'
import { fuenteArchivo } from './fuentes'

const eventosE1 = e1 as unknown as Evento[]

describe('replay e1.json (RF-F1-05)', () => {
  it('tiene seq 1..n sin huecos y la secuencia de tipos de E1', () => {
    expect(eventosE1.map((e) => e.seq)).toEqual(eventosE1.map((_, i) => i + 1))
    const tipos = eventosE1.map((e) => e.tipo)
    expect(tipos[0]).toBe('run.iniciado')
    expect(tipos.at(-3)).toBe('supervisor.consolidado')
    expect(tipos.at(-2)).toBe('plan.listo')
    expect(tipos.at(-1)).toBe('humano.decision_requerida')
  })
})

describe('reducir', () => {
  it('E1 queda esperando decisión con plan RECOMENDADO y todo CUMPLE', () => {
    const s = reducirTodos(eventosE1)
    expect(s.estadoRun).toBe('ESPERANDO_DECISION')
    expect(s.estadoSistema).toBe('RECOMENDADO')
    expect(s.plan?.cambios).toEqual([])
    expect(s.decisionRequerida).toEqual({ plan_id: 'plan-e1', solo_rechazo: false })
    expect(s.resultadosControl.map((c) => c.estado)).toEqual(['CUMPLE', 'CUMPLE', 'CUMPLE'])
    for (const r of Object.values(s.resultadosRequisito)) expect(r.evidencia.length).toBeGreaterThan(0)
    expect(s.evaluacion?.peligros[0].incidentes_similares).toEqual(['inc-007', 'inc-021'])
  })

  it('marca a los 4 agentes como completados y guarda sus herramientas', () => {
    const s = reducirTodos(eventosE1)
    for (const a of Object.values(s.agentes)) expect(a.estado).toBe('completado')
    expect(s.agentes.riesgo.herramientas.map((h) => h.nombre)).toEqual(['buscar_incidentes'])
    expect(s.agentes.personal.herramientas).toHaveLength(2)
  })

  it('Personal y Equipo se ven trabajando a la vez (RF-F1-31)', () => {
    const hastaAmbos = eventosE1.slice(0, eventosE1.findIndex((e) => e.seq === 7))
    const s = reducirTodos(hastaAmbos)
    expect(s.agentes.personal.estado).toBe('trabajando')
    expect(s.agentes.equipo.estado).toBe('trabajando')
  })

  it('es idempotente: reenviar eventos (reconexión SSE) no cambia el estado', () => {
    const una = reducirTodos(eventosE1)
    const conRepetidos = reducirTodos([...eventosE1.slice(0, 8), ...eventosE1])
    expect(conRepetidos).toEqual(una)
    expect(reducirTodos(eventosE1, una)).toBe(una)
  })

  it('es puro: no muta el estado anterior', () => {
    const inicial = estadoInicial()
    const copia = structuredClone(inicial)
    reducir(inicial, eventosE1[0])
    expect(inicial).toEqual(copia)
  })

  it('run.error marca en error a los agentes que trabajaban', () => {
    const parcial = reducirTodos(eventosE1.slice(0, 2))
    const s = reducir(parcial, {
      run_id: 'replay-e1', seq: 99, ts: '2026-10-17T15:00:09.000Z', tipo: 'run.error', actor: 'sistema',
      payload: { mensaje: 'tiempo agotado' },
    })
    expect(s.estadoRun).toBe('ERROR')
    expect(s.agentes.riesgo.estado).toBe('error')
    expect(s.agentes.personal.estado).toBe('inactivo')
  })

  it('al pedir campo el Supervisor deja de trabajar (orquestador stub de P1, sin plan.listo)', () => {
    const parcial = reducirTodos(eventosE1.slice(0, 1))
    const s = reducir(parcial, {
      run_id: 'replay-e1', seq: 2, ts: '2026-10-17T15:00:01.000Z', tipo: 'humano.campo_requerido',
      actor: 'capataz:agente-supervisor', payload: { preguntas: [{ requisito_id: 'req-x', pregunta: '¿Ok?' }] },
    })
    expect(s.estadoRun).toBe('ESPERANDO_CAMPO')
    expect(s.agentes.supervisor.estado).toBe('completado')
  })

  it('normaliza ids de agente', () => {
    expect(idAgente('capataz:agente-equipo')).toBe('equipo')
    expect(idAgente('riesgo')).toBe('riesgo')
    expect(idAgente('sistema')).toBeNull()
  })
})

describe('fuenteArchivo', () => {
  afterEach(() => vi.useRealTimers())

  it('emite todos los eventos en orden y deja el mismo estado que reducirTodos', () => {
    vi.useFakeTimers()
    let s = estadoInicial()
    const conexiones: string[] = []
    fuenteArchivo(eventosE1, { velocidad: 4 })({
      onEvento: (e) => (s = reducir(s, e)),
      onConexion: (c) => conexiones.push(c),
    })
    vi.runAllTimers()
    expect(s).toEqual(reducirTodos(eventosE1))
    expect(conexiones).toEqual(['abierta', 'cerrada'])
  })

  it('cerrar detiene la reproducción', () => {
    vi.useFakeTimers()
    const vistos: number[] = []
    const cerrar = fuenteArchivo(eventosE1)({ onEvento: (e) => vistos.push(e.seq) })
    vi.advanceTimersByTime(0)
    cerrar()
    vi.runAllTimers()
    expect(vistos).toEqual([1])
  })
})
