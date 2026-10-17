// El plan sobre el que se decide (RF-F2-21, RT-04).
//
// El backend entrega `plan` (el original, que en un conflicto puede ser BLOQUEADO) y `planes_alternativos`
// (los verificados, el mejor primero), y `decision_requerida.plan_id` apunta al candidato. El estado que
// importa (bloqueado, solo rechazo, qué comparar) es el del plan elegido, no el del original: con un
// original BLOQUEADO y una alternativa RECOMENDADO se puede aprobar la alternativa.
import type { Plan } from '@/api/types'

export function planActivo(planes: Plan[], planId: string): Plan | undefined {
  return planes.find((p) => p.id === planId) ?? planes[0]
}

/** Planes entre los que la persona elige: los aprobables, sin el original bloqueado. Si ninguno lo es, todos. */
export function planesElegibles(planes: Plan[]): Plan[] {
  const viables = planes.filter((p) => p.estado_sistema !== 'BLOQUEADO')
  return viables.length > 0 ? viables : planes
}

/**
 * Id del plan sobre el que se decide. Una decisión ya tomada manda (tras `humano.decision_tomada` el reductor
 * borra `decisionRequerida`, y sin esto se volvería a mirar el plan original); luego el elegido a mano, el que
 * pide el backend y, por último, el primero.
 */
export function idPlanDecision({ decision, elegido, requerida, plan }: {
  decision: { plan_id: string } | null
  elegido: string | null
  requerida: { plan_id: string } | null
  plan: { id: string } | null | undefined
}): string {
  return decision?.plan_id ?? elegido ?? requerida?.plan_id ?? plan?.id ?? ''
}
