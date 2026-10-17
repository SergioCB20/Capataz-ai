// Progreso de la evaluación en 4 pasos, derivado del estado (no inventa avances).
import { Check } from 'lucide-react'
import type { EstadoUI } from '@/eventos/reductor'
import { cn } from '@/lib/utils'

interface Paso {
  titulo: string
  detalle: string
  hecho: boolean
}

export function pasosDe(estado: EstadoUI): Paso[] {
  const nIncidentes = new Set(estado.evaluacion?.peligros.flatMap((p) => p.incidentes_similares) ?? []).size
  const nPeligros = estado.evaluacion?.peligros.length ?? 0
  const verificadas = estado.alternativas.filter((a) => a.cumple_bloqueantes === true).length
  const hayConflicto = estado.conflictos.length > 0
  const decidido = !!estado.decision || ['APROBADA', 'RECHAZADA', 'BLOQUEADA'].includes(estado.estadoRun ?? '')

  return [
    {
      titulo: 'Riesgo',
      detalle: estado.evaluacion ? `${nPeligros} peligro${nPeligros === 1 ? '' : 's'} · ${nIncidentes} incidente${nIncidentes === 1 ? '' : 's'} similar${nIncidentes === 1 ? '' : 'es'}` : 'Analizando peligros…',
      hecho: !!estado.evaluacion,
    },
    {
      titulo: 'Verificación',
      detalle: estado.resultadosControl.length
        ? hayConflicto
          ? `${estado.conflictos.length} requisito${estado.conflictos.length === 1 ? '' : 's'} bloqueante${estado.conflictos.length === 1 ? '' : 's'} falla${estado.conflictos.length === 1 ? '' : 'n'}`
          : 'Controles consolidados'
        : 'Personal y Equipo verificando…',
      hecho: estado.resultadosControl.length > 0,
    },
    {
      titulo: estado.preguntasCampo.length || estado.estadoRun === 'ESPERANDO_CAMPO' ? 'Confirmación en campo' : 'Alternativas',
      detalle: estado.estadoRun === 'ESPERANDO_CAMPO'
        ? 'Falta confirmar en la labor'
        : hayConflicto
          ? estado.plan ? `${verificadas} de ${estado.alternativas.length} verificadas` : 'Buscando alternativas…'
          : estado.plan ? 'No hicieron falta' : 'Pendiente',
      hecho: !!estado.plan && estado.estadoRun !== 'ESPERANDO_CAMPO',
    },
    {
      titulo: 'Tu decisión',
      detalle: decidido
        ? estado.decision?.decision === 'aprobar' ? 'Plan aprobado' : 'Plan rechazado'
        : estado.decisionRequerida ? 'Esperando tu decisión' : 'Pendiente',
      hecho: decidido,
    },
  ]
}

export function ProgresoEvaluacion({ estado }: { estado: EstadoUI }) {
  const pasos = pasosDe(estado)
  const actual = pasos.findIndex((p) => !p.hecho)
  return (
    <section aria-label="Progreso de la evaluación" className="rounded-[28px] bg-white px-6 py-5 sm:px-8">
      <ol className="m-0 grid list-none grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-3 p-0">
        {pasos.map((p, i) => (
          <li key={p.titulo} className="flex items-center gap-3" aria-current={i === actual ? 'step' : undefined}>
            <span
              className={cn(
                'grid size-9 flex-none place-items-center rounded-full text-sm font-extrabold',
                p.hecho ? 'bg-tinta text-white' : i === actual ? 'bg-acento text-white ring-[5px] ring-acento-suave' : 'bg-segmento text-tenue',
              )}
            >
              {p.hecho ? <Check aria-label="hecho" className="size-[18px]" strokeWidth={3} /> : i + 1}
            </span>
            <span className="flex min-w-0 flex-col">
              <span className="text-[15px] font-extrabold">{p.titulo}</span>
              <span className="text-[13px] text-tenue">{p.detalle}</span>
            </span>
          </li>
        ))}
      </ol>
    </section>
  )
}
