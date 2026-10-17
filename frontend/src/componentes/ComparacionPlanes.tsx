// «Qué cambia» (RF-F2-31): asignación original frente al plan elegido, campo a campo.
import type { Asignacion, Plan } from '@/api/types'
import { cn } from '@/lib/utils'

function Campo({ titulo, antes, despues }: { titulo: string; antes: string; despues: string }) {
  const cambia = antes !== despues
  return (
    <div className="rounded-2xl bg-white px-3.5 py-3">
      <div className="text-xs font-bold text-tenue">{titulo}</div>
      <div className={cn('mt-1 text-sm text-[#6E6A7C]', cambia && 'line-through')}>{antes || '—'}</div>
      <div className="mt-0.5 text-[15px] font-extrabold">{cambia ? despues || '—' : 'Sin cambio'}</div>
    </div>
  )
}

export function ComparacionPlanes({ original, plan, nombreRecurso }: {
  original: Asignacion
  plan: Plan
  nombreRecurso: (valor: string) => string
}) {
  const lista = (ids: string[]) => ids.map(nombreRecurso).join(', ')
  const turno = plan.cambios.find((c) => c.tipo === 'reprogramar_turno')
  return (
    <div className="rounded-[20px] bg-campo px-5 py-[18px]">
      <div className="mb-3 text-[15px] font-extrabold">
        Qué cambia con <span className="font-mono">{plan.id}</span>
      </div>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-3">
        {turno && <Campo titulo="Turno" antes={nombreRecurso(turno.desde)} despues={nombreRecurso(turno.hacia)} />}
        <Campo titulo="Personas" antes={lista(original.personas)} despues={lista(plan.asignacion.personas)} />
        <Campo titulo="Equipos" antes={lista(original.equipos)} despues={lista(plan.asignacion.equipos)} />
      </div>
      {plan.cambios.length > 0 && (
        <ul className="mt-3 grid gap-1.5 p-0 text-xs text-tenue">
          {plan.cambios.map((c, i) => (
            <li key={i} className="list-none">Por qué: {c.motivo}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
