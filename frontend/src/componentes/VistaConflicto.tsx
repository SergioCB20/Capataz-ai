// Conflicto y alternativas (RF-F2-30, 35, 08, 21): causas con evidencia; alternativas por ronda con el
// veredicto de las HERRAMIENTAS separado de la explicación del LLM; las verificadas se pueden elegir.
import { motion } from 'motion/react'
import { CircleCheck, CircleX, Loader2, Star } from 'lucide-react'
import type { Alternativa, Evidencia, Plan, TipoCambio } from '@/api/types'
import { cn } from '@/lib/utils'
import { Pastilla } from './insignias'

export const TIPO_CAMBIO: Record<TipoCambio, string> = {
  reprogramar_turno: 'Reprogramar turno',
  equipo_equivalente: 'Equipo equivalente',
  certificacion_equivalente: 'Otra persona',
}

function Veredicto({ alt }: { alt: Alternativa }) {
  if (alt.cumple_bloqueantes === null) return <Pastilla tono="neutro" icono={Loader2} girar texto="Verificando" />
  if (alt.cumple_bloqueantes) return <Pastilla tono="ok" icono={CircleCheck} texto="Verificada" />
  return <Pastilla tono="peligro" icono={CircleX} texto="Falló" />
}

export function VistaConflicto({ conflictos, nombreControl, nombreRecurso, ronda, alternativas, planes, elegido, onElegir, puedeElegir, enCurso, children }: {
  conflictos: { control_id: string; requisito_id: string; causa: string; evidencia: Evidencia[] }[]
  nombreControl: (id: string) => string
  nombreRecurso: (valor: string) => string
  ronda: 1 | 2 | null
  alternativas: Alternativa[]
  /** Planes candidatos (Plan.id == Alternativa.id). */
  planes: Plan[]
  elegido: string | null
  onElegir: (planId: string) => void
  puedeElegir: boolean
  enCurso: boolean
  children?: React.ReactNode
}) {
  const rondas = [...new Set(alternativas.map((a) => a.ronda))].sort()
  return (
    <section aria-labelledby="alt" className="flex flex-col gap-4 rounded-[28px] bg-white px-6 py-6 sm:px-7">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="alt" className="text-lg font-extrabold">Conflicto y alternativas</h2>
        {ronda && (
          <Pastilla tono={enCurso ? 'aviso' : 'neutro'} icono={enCurso ? Loader2 : CircleCheck} girar={enCurso} texto={`Ronda ${ronda} de 2`} />
        )}
      </div>

      <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-3">
        {conflictos.map((c) => (
          <div key={`${c.control_id}/${c.requisito_id}`} className="rounded-[18px] bg-mal-fondo px-4 py-3.5 text-sm leading-snug text-[#6E1414]">
            <b>{nombreControl(c.control_id)}</b>
            <br />
            {c.causa}
            {c.evidencia.length > 0 && (
              <ul className="mt-2 space-y-1 text-xs">
                {c.evidencia.map((ev, i) => (
                  <li key={i} className="flex flex-wrap items-center gap-1">
                    <span className="font-mono">{ev.registro}</span> · {ev.campo}: <b>{String(ev.valor)}</b>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>

      {alternativas.length === 0 ? (
        <p className="flex items-center gap-2 text-sm text-tenue">
          <Loader2 aria-hidden className="size-4 animate-spin" /> El Supervisor está pidiendo alternativas al LLM…
        </p>
      ) : (
        rondas.map((r) => (
          <div key={r} aria-label={`Alternativas de la ronda ${r}`} role="group">
            <h3 className="mb-2 text-xs font-bold text-tenue">Ronda {r}</h3>
            <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-3.5">
              {alternativas.filter((a) => a.ronda === r).map((a, i) => {
                const plan = planes.find((p) => p.id === a.id)
                const sel = elegido === a.id
                // Solo se aprueba un plan RECOMENDADO. P2 recalcula tras el campo solo la mejor
                // alternativa; las demás verificadas quedan como respaldo (no elegibles).
                const recomendada = plan?.estado_sistema === 'RECOMENDADO'
                const esLaMejor = planes[0]?.id === a.id
                return (
                  <motion.article
                    key={a.id}
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0, transition: { delay: i * 0.08 } }}
                    className={cn(
                      'flex flex-col gap-3 rounded-[22px] border-2 p-[18px]',
                      sel ? 'border-acento bg-acento-fondo' : a.cumple_bloqueantes === false ? 'border-dashed border-[#E3C9C7] bg-[#FBFAFD]' : 'border-linea bg-white',
                    )}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-mono text-[13px]">{a.id}</span>
                      <span className="flex flex-wrap items-center gap-1.5">
                        {plan && esLaMejor && <Pastilla tono="ok" icono={Star} texto="Recomendada" />}
                        {plan && !esLaMejor && <Pastilla tono="neutro" icono={CircleCheck} texto="Opción de respaldo" />}
                        <Veredicto alt={a} />
                      </span>
                    </div>
                    <ul className="m-0 flex list-none flex-col gap-2 p-0">
                      {a.cambios.map((c, j) => (
                        <li key={j} className="text-[13px] leading-snug">
                          <span className="block text-[11px] font-bold tracking-wide text-tenue uppercase">{TIPO_CAMBIO[c.tipo]}</span>
                          <span className="text-[#6E6A7C] line-through">{nombreRecurso(c.desde)}</span> → <b>{nombreRecurso(c.hacia)}</b>
                        </li>
                      ))}
                    </ul>
                    {a.cumple_bloqueantes === false && a.motivo_fallo && (
                      <p className="m-0 rounded-xl bg-mal-fondo px-3 py-2.5 text-[13px] leading-snug text-[#6E1414]">
                        <b>Motivo (herramienta):</b> {a.motivo_fallo}
                      </p>
                    )}
                    <p className="m-0 rounded-xl bg-segmento px-3 py-2.5 text-[13px] leading-snug">
                      <b>Por qué la propone el LLM:</b> {a.explicacion}
                    </p>
                    {plan && !recomendada && !esLaMejor && (
                      <p className="m-0 mt-auto rounded-xl bg-acento-fondo px-3 py-2.5 text-[13px] leading-snug text-acento-texto">
                        También pasó la verificación de personas y equipos. Queda como respaldo: para usarla habría que confirmar su campo por separado.
                      </p>
                    )}
                    {plan && (recomendada || esLaMejor) && (
                      <button
                        type="button"
                        onClick={() => onElegir(a.id)}
                        aria-pressed={sel}
                        disabled={!puedeElegir || !recomendada}
                        className={cn(
                          'mt-auto min-h-11 rounded-full text-sm font-extrabold transition-colors focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-acento disabled:cursor-not-allowed disabled:opacity-60',
                          sel ? 'bg-acento text-white' : 'border-[1.5px] border-tinta bg-white text-tinta hover:bg-segmento',
                        )}
                      >
                        {sel ? 'Plan elegido' : 'Elegir este plan'}
                      </button>
                    )}
                  </motion.article>
                )
              })}
            </div>
          </div>
        ))
      )}
      {children}
    </section>
  )
}
