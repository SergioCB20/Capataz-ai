// Cajón de evidencia (RF-F1-33): evidencia, agente que verificó, fuente e incidentes similares.
import type { Incidente } from '@/api/types'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import type { FilaControl, FilaRequisito } from '@/eventos/vista'
import { EstadoControlBadge, InsigniaSimulado, nombreActor } from './insignias'

const TIPO_FUENTE = { normativa: 'Normativa', guia: 'Guía', simulado: 'Dato simulado' } as const

export function CajonEvidencia({ seleccion, incidentes, onCerrar }: {
  seleccion: { control: FilaControl; requisito: FilaRequisito } | null
  incidentes: (Incidente | { id: string })[]
  onCerrar: () => void
}) {
  const r = seleccion?.requisito.resultado ?? null
  return (
    <Sheet open={!!seleccion} onOpenChange={(abierto) => !abierto && onCerrar()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-md">
        {seleccion && (
          <>
            <SheetHeader>
              <SheetTitle>{seleccion.requisito.requisito.descripcion}</SheetTitle>
              <SheetDescription>Control: {seleccion.control.nombre}</SheetDescription>
            </SheetHeader>
            <div className="grid gap-5 px-4 pb-6 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <EstadoControlBadge estado={r?.estado ?? null} />
                {r && <span className="text-muted-foreground">Verificado por <b>{nombreActor(r.verificado_por)}</b></span>}
              </div>
              {r?.detalle && <p>{r.detalle}</p>}

              <section>
                <h3 className="mb-2 font-medium">Evidencia</h3>
                {!r ? (
                  <p className="text-muted-foreground">Aún sin resultado: el requisito está en verificación.</p>
                ) : r.evidencia.length === 0 ? (
                  <p className="text-muted-foreground">Sin evidencia registrada (por eso no puede ser CUMPLE).</p>
                ) : (
                  <ul className="space-y-2">
                    {r.evidencia.map((ev, i) => (
                      <li key={i} className="rounded-md border p-2">
                        <div className="font-mono text-xs">{ev.registro}</div>
                        <div className="mt-1">
                          <span className="text-muted-foreground">{ev.campo}:</span> <b>{ev.valor}</b>
                        </div>
                        <div className="mt-1 flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
                          {TIPO_FUENTE[ev.fuente.tipo]} · {ev.fuente.url ? <a className="underline" href={ev.fuente.url} target="_blank" rel="noreferrer">{ev.fuente.referencia}</a> : ev.fuente.referencia}
                          <InsigniaSimulado fuente={ev.fuente} />
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              <section>
                <h3 className="mb-2 font-medium">Incidentes similares</h3>
                {incidentes.length === 0 ? (
                  <p className="text-muted-foreground">El Agente Riesgo no asoció incidentes a este control.</p>
                ) : (
                  <ul className="space-y-2">
                    {incidentes.map((inc) => (
                      <li key={inc.id} className="rounded-md border p-2">
                        <div className="flex flex-wrap items-center justify-between gap-1">
                          <span className="font-mono text-xs">{inc.id}</span>
                          <InsigniaSimulado fuente={'fuente' in inc ? inc.fuente : null} />
                        </div>
                        {'descripcion' in inc ? (
                          <>
                            <p className="mt-1">{inc.descripcion}</p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {inc.fecha} · {inc.planta} · nivel real {inc.nivel_real}, potencial {inc.nivel_potencial} · causa: {inc.causa_raiz}
                            </p>
                          </>
                        ) : (
                          <p className="mt-1 text-muted-foreground">Detalle no disponible en el catálogo cargado.</p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}
