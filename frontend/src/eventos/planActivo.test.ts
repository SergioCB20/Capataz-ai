import { describe, expect, it } from 'vitest'
import type { Plan } from '@/api/types'
import { idPlanDecision, planActivo, planesElegibles } from './planActivo'

const plan = (id: string, estado_sistema: Plan['estado_sistema']) => ({ id, estado_sistema }) as Plan

describe('planActivo', () => {
  it('conflicto con alternativa verificada: el plan de decisión es la alternativa, no el original bloqueado', () => {
    const planes = [plan('plan-original', 'BLOQUEADO'), plan('alt-b', 'RECOMENDADO')]
    expect(planActivo(planes, 'alt-b')?.estado_sistema).toBe('RECOMENDADO')
  })

  it('sin alternativa segura (E3): el plan es el original y sigue BLOQUEADO', () => {
    expect(planActivo([plan('plan-e3', 'BLOQUEADO')], 'plan-e3')?.estado_sistema).toBe('BLOQUEADO')
  })

  it('forma de los fixtures: el plan ya es la alternativa recomendada', () => {
    const planes = [plan('plan-e2-alt-1', 'RECOMENDADO'), plan('plan-e2-alt-3', 'RECOMENDADO')]
    expect(planActivo(planes, 'plan-e2-alt-1')?.id).toBe('plan-e2-alt-1')
  })

  it('al elegir otro plan, el estado es el del elegido', () => {
    const planes = [plan('plan-original', 'BLOQUEADO'), plan('alt-a', 'REQUIERE_CAMPO'), plan('alt-b', 'RECOMENDADO')]
    expect(planActivo(planes, 'alt-a')?.estado_sistema).toBe('REQUIERE_CAMPO')
  })

  it('un id desconocido o vacío cae al primer plan; sin planes no hay plan', () => {
    expect(planActivo([plan('x', 'RECOMENDADO')], '')?.id).toBe('x')
    expect(planActivo([], 'x')).toBeUndefined()
  })
})

describe('planesElegibles', () => {
  it('con un original bloqueado y una alternativa verificada, solo se ofrece la alternativa', () => {
    const planes = [plan('plan-original', 'BLOQUEADO'), plan('alt-b', 'RECOMENDADO')]
    expect(planesElegibles(planes).map((p) => p.id)).toEqual(['alt-b'])
  })

  it('con varias alternativas aprobables se ofrecen todas; las bloqueadas no', () => {
    const planes = [plan('o', 'BLOQUEADO'), plan('a', 'RECOMENDADO'), plan('b', 'REQUIERE_CAMPO')]
    expect(planesElegibles(planes).map((p) => p.id)).toEqual(['a', 'b'])
  })

  it('sin alternativa segura (E3) queda el único plan, bloqueado', () => {
    expect(planesElegibles([plan('plan-e3', 'BLOQUEADO')]).map((p) => p.id)).toEqual(['plan-e3'])
  })

  it('los fixtures con dos planes recomendados siguen ofreciendo los dos', () => {
    expect(planesElegibles([plan('x', 'RECOMENDADO'), plan('y', 'RECOMENDADO')])).toHaveLength(2)
  })
})

describe('idPlanDecision', () => {
  const original = { id: 'plan-original' }

  it('mientras se espera la decisión usa el plan que pide el backend, no el original', () => {
    expect(idPlanDecision({ decision: null, elegido: null, requerida: { plan_id: 'alt-b' }, plan: original })).toBe('alt-b')
  })

  it('tras tomar la decisión sigue siendo el plan decidido (el reductor ya borró decisionRequerida)', () => {
    expect(idPlanDecision({ decision: { plan_id: 'alt-b' }, elegido: null, requerida: null, plan: original })).toBe('alt-b')
  })

  it('el plan elegido a mano gana a lo que pide el backend', () => {
    expect(idPlanDecision({ decision: null, elegido: 'alt-a', requerida: { plan_id: 'alt-b' }, plan: original })).toBe('alt-a')
  })

  it('sin decisión ni petición cae al plan; sin nada, vacío', () => {
    expect(idPlanDecision({ decision: null, elegido: null, requerida: null, plan: original })).toBe('plan-original')
    expect(idPlanDecision({ decision: null, elegido: null, requerida: null, plan: null })).toBe('')
  })
})
