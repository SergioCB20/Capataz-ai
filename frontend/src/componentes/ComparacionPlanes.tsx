// Comparación de la asignación original vs. el «Plan (PTW borrador)» (RF-F2-31) y elección
// del plan cuando hay varias alternativas verificadas (RF-F2-21).
import { ArrowRight, Minus, Plus } from 'lucide-react'
import type { Catalogo, Plan, Tarea } from '@/api/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { cn } from '@/lib/utils'
import { EstadoSistemaBadge } from './insignias'
import { TIPO_CAMBIO } from './VistaConflicto'

function Diferencia({ titulo, antes, despues, nombre }: {
  titulo: string; antes: string[]; despues: string[]; nombre: (id: string) => string
}) {
  const quitados = antes.filter((x) => !despues.includes(x))
  const agregados = despues.filter((x) => !antes.includes(x))
  const iguales = antes.filter((x) => despues.includes(x))
  return (
    <div className="grid grid-cols-[6rem_minmax(0,1fr)_auto_minmax(0,1fr)] items-start gap-2 text-sm">
      <span className="text-muted-foreground">{titulo}</span>
      <ul>
        {antes.length === 0 && <li className="text-muted-foreground">—</li>}
        {antes.map((id) => (
          <li key={id} className={cn('flex items-center gap-1', quitados.includes(id) && 'text-red-700 line-through dark:text-red-300')}>
            {quitados.includes(id) && <Minus aria-label="se quita" className="size-3.5 shrink-0" />}
            {nombre(id)}
          </li>
        ))}
      </ul>
      <ArrowRight aria-hidden className="mt-0.5 size-4 text-muted-foreground" />
      <ul>
        {despues.length === 0 && <li className="text-muted-foreground">—</li>}
        {[...iguales, ...agregados].map((id) => (
          <li key={id} className={cn('flex items-center gap-1', agregados.includes(id) && 'font-medium text-emerald-700 dark:text-emerald-300')}>
            {agregados.includes(id) && <Plus aria-label="se agrega" className="size-3.5 shrink-0" />}
            {nombre(id)}
          </li>
        ))}
      </ul>
    </div>
  )
}

export function ComparacionPlanes({ tarea, planes, elegido, onElegir, catalogo, puedeElegir }: {
  tarea: Tarea
  planes: Plan[]
  elegido: string
  onElegir: (planId: string) => void
  catalogo: Catalogo
  puedeElegir: boolean
}) {
  const plan = planes.find((p) => p.id === elegido) ?? planes[0]
  if (!plan) return null
  const persona = (id: string) => catalogo.personas.find((p) => p.id === id)?.nombre ?? id
  const equipo = (id: string) => catalogo.equipos.find((e) => e.id === id)?.nombre ?? id

  return (
    <Card>
      <CardHeader>
        <CardTitle>Plan (PTW borrador) frente a la asignación original</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        {planes.length > 1 && (
          <fieldset>
            <legend className="mb-2 text-sm">Hay {planes.length} alternativas verificadas. Elige cuál aprobar:</legend>
            <RadioGroup value={plan.id} onValueChange={onElegir} className="grid gap-2 sm:grid-cols-2" disabled={!puedeElegir}>
              {planes.map((p) => (
                <label key={p.id} className={cn('flex cursor-pointer items-start gap-2 rounded-md border p-2 text-sm', p.id === plan.id && 'border-primary')}>
                  <RadioGroupItem value={p.id} className="mt-0.5" />
                  <span className="grid gap-1">
                    <span className="flex flex-wrap items-center gap-2 font-mono text-xs">{p.id} <EstadoSistemaBadge estado={p.estado_sistema} /></span>
                    <span className="text-muted-foreground">{p.cambios.map((c) => TIPO_CAMBIO[c.tipo]).join(' + ') || 'Sin cambios'}</span>
                  </span>
                </label>
              ))}
            </RadioGroup>
          </fieldset>
        )}

        <div className="grid gap-2 rounded-md border p-3">
          <div className="grid grid-cols-[6rem_minmax(0,1fr)_auto_minmax(0,1fr)] gap-2 text-xs font-medium text-muted-foreground">
            <span />
            <span>Original</span>
            <span />
            <span>Plan {plan.id}</span>
          </div>
          <Diferencia titulo="Personas" antes={tarea.asignacion.personas} despues={plan.asignacion.personas} nombre={persona} />
          <Diferencia titulo="Equipos" antes={tarea.asignacion.equipos} despues={plan.asignacion.equipos} nombre={equipo} />
        </div>

        {plan.cambios.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sin cambios frente a la asignación original.</p>
        ) : (
          <ul className="grid gap-2 text-sm">
            {plan.cambios.map((c, i) => (
              <li key={i} className="rounded-md bg-muted p-2">
                <b>{TIPO_CAMBIO[c.tipo]}:</b> {c.desde} → {c.hacia}
                <div className="text-xs text-muted-foreground">Por qué: {c.motivo}</div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
