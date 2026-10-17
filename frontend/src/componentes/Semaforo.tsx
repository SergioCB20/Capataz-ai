// Semáforo de controles (RF-F1-32): icono + texto, si es bloqueante e insignia «simulado».
// Cada requisito abre el cajón de evidencia (RF-F1-33).
import { ChevronRight, ShieldAlert } from 'lucide-react'
import type { FilaControl, FilaRequisito } from '@/eventos/vista'
import { EstadoControlBadge, InsigniaSimulado, Pastilla } from './insignias'

const TIPO_REQUISITO = { competencia: 'Competencia', equipo: 'Equipo', condicion_campo: 'Condición de campo' } as const

export function Semaforo({ filas, nombrePeligro, onElegir }: {
  filas: FilaControl[]
  nombrePeligro: (id: string | null) => string
  onElegir: (control: FilaControl, requisito: FilaRequisito) => void
}) {
  if (filas.length === 0) {
    return <p className="p-4 text-sm text-muted-foreground">El Agente Riesgo aún no ha identificado los controles que aplican.</p>
  }
  return (
    <ul className="divide-y" aria-label="Controles críticos">
      {filas.map((c) => (
        <li key={c.controlId} className="py-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="font-medium">{c.nombre}</div>
              <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                {nombrePeligro(c.peligroId)}
                {c.bloqueante && <Pastilla tono="neutro" icono={ShieldAlert} texto="Bloqueante" />}
                <InsigniaSimulado fuente={c.fuente} />
              </div>
            </div>
            <EstadoControlBadge estado={c.estado} />
          </div>
          <ul className="mt-2 space-y-1">
            {c.requisitos.map((r) => (
              <li key={r.requisito.id}>
                <button
                  type="button"
                  onClick={() => onElegir(c, r)}
                  className="flex w-full items-center justify-between gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <span className="min-w-0">
                    <span className="mr-2 text-xs text-muted-foreground">{TIPO_REQUISITO[r.requisito.tipo]}</span>
                    {r.requisito.descripcion}
                  </span>
                  <span className="flex shrink-0 items-center gap-1">
                    <EstadoControlBadge estado={r.resultado?.estado ?? null} />
                    <ChevronRight aria-hidden className="size-4 text-muted-foreground" />
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </li>
      ))}
    </ul>
  )
}
