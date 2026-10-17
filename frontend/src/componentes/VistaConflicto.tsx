// Vista de conflicto (RF-F2-30, RF-F2-35, RF-F2-08): control en rojo con causa y evidencia;
// alternativas lado a lado con cambios, veredicto de las HERRAMIENTAS y explicación del LLM por separado.
import { ArrowRight, CircleCheck, CircleX, Loader2, Sparkles, TriangleAlert } from 'lucide-react'
import type { Alternativa, Evidencia, TipoCambio } from '@/api/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { InsigniaSimulado, Pastilla } from './insignias'

export const TIPO_CAMBIO: Record<TipoCambio, string> = {
  reprogramar_turno: 'Reprogramar turno',
  equipo_equivalente: 'Equipo equivalente',
  certificacion_equivalente: 'Certificación equivalente',
}

function Veredicto({ alt }: { alt: Alternativa }) {
  if (alt.cumple_bloqueantes === null) return <Pastilla tono="neutro" icono={Loader2} girar texto="Verificando con herramientas" />
  if (alt.cumple_bloqueantes) return <Pastilla tono="ok" icono={CircleCheck} texto="Verificada con herramientas" />
  return <Pastilla tono="peligro" icono={CircleX} texto="Falló la verificación" />
}

export function VistaConflicto({ conflictos, nombreControl, nombreRecurso, ronda, alternativas, enCurso }: {
  conflictos: { control_id: string; requisito_id: string; causa: string; evidencia: Evidencia[] }[]
  nombreControl: (id: string) => string
  nombreRecurso: (valor: string) => string
  ronda: 1 | 2 | null
  alternativas: Alternativa[]
  enCurso: boolean
}) {
  const rondas = [...new Set(alternativas.map((a) => a.ronda))].sort()
  return (
    <Card className="border-red-300 dark:border-red-800">
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center justify-between gap-2">
          <span className="flex items-center gap-2">
            <TriangleAlert aria-hidden className="size-5 text-red-600" />
            {conflictos.length > 1 ? `${conflictos.length} requisitos bloqueantes no se cumplen` : 'Conflicto en un control bloqueante'}
          </span>
          {ronda && (
            <Pastilla
              tono={enCurso ? 'aviso' : 'neutro'}
              icono={enCurso ? Loader2 : CircleCheck}
              girar={enCurso}
              texto={`Ronda de resolución ${ronda}/2`}
            />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 text-sm">
        {conflictos.map((conflicto) => (
          <div key={`${conflicto.control_id}/${conflicto.requisito_id}`} className="rounded-md border border-red-300 bg-red-50 p-3 text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-100">
            <div className="font-medium">{nombreControl(conflicto.control_id)}</div>
            <p className="mt-1">{conflicto.causa}</p>
            {conflicto.evidencia.length > 0 && (
              <ul className="mt-2 space-y-1 text-xs">
                {conflicto.evidencia.map((ev, i) => (
                  <li key={i} className="flex flex-wrap items-center gap-1">
                    <span className="font-mono">{ev.registro}</span> · {ev.campo}: <b>{ev.valor}</b>
                    <InsigniaSimulado fuente={ev.fuente} />
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}

        {alternativas.length === 0 ? (
          <p className="flex items-center gap-2 text-muted-foreground">
            <Loader2 aria-hidden className="size-4 animate-spin" /> El Supervisor está pidiendo alternativas al LLM…
          </p>
        ) : (
          rondas.map((r) => (
            <section key={r} aria-label={`Alternativas de la ronda ${r}`}>
              <h3 className="mb-2 text-xs font-medium text-muted-foreground">Ronda {r}</h3>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {alternativas.filter((a) => a.ronda === r).map((a) => (
                  <article
                    key={a.id}
                    className={cn(
                      'grid content-start gap-3 rounded-xl border p-3',
                      a.cumple_bloqueantes === true && 'border-emerald-400',
                      a.cumple_bloqueantes === false && 'border-red-300 opacity-90',
                    )}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-mono text-xs">{a.id}</span>
                      <Veredicto alt={a} />
                    </div>
                    <ul className="grid gap-1.5">
                      {a.cambios.map((c, i) => (
                        <li key={i}>
                          <div className="text-xs font-medium text-muted-foreground">{TIPO_CAMBIO[c.tipo]}</div>
                          <div className="flex flex-wrap items-center gap-1">
                            <span className="line-through decoration-red-400">{nombreRecurso(c.desde)}</span>
                            <ArrowRight aria-hidden className="size-3.5" />
                            <b>{nombreRecurso(c.hacia)}</b>
                          </div>
                          <div className="text-xs text-muted-foreground">{c.motivo}</div>
                        </li>
                      ))}
                    </ul>
                    {a.cumple_bloqueantes === false && a.motivo_fallo && (
                      <p className="rounded-md bg-red-50 p-2 text-xs text-red-800 dark:bg-red-950 dark:text-red-200">
                        <b>Motivo del fallo (herramienta):</b> {a.motivo_fallo}
                      </p>
                    )}
                    <div className="rounded-md bg-muted p-2 text-xs">
                      <div className="mb-0.5 flex items-center gap-1 font-medium">
                        <Sparkles aria-hidden className="size-3" /> Explicación (LLM, no es el veredicto)
                      </div>
                      {a.explicacion}
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ))
        )}
      </CardContent>
    </Card>
  )
}
