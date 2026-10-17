// Estado bloqueado (E3, RF-F2-33): por qué, qué se intentó y a quién escalar.
// La barra de decisión ya solo ofrece «Rechazar» (RT-04).
import { Megaphone, OctagonX } from 'lucide-react'
import type { Alternativa } from '@/api/types'

export function EstadoBloqueado({ motivo, causas, alternativas, escalamiento }: {
  /** `Plan.motivo` del plan original (P2). */
  motivo: string | null | undefined
  causas: string[]
  alternativas: Alternativa[]
  escalamiento: string | null | undefined
}) {
  const fallidas = alternativas.filter((a) => a.cumple_bloqueantes === false)
  const rondas = new Set(alternativas.map((a) => a.ronda)).size
  return (
    <section role="alert" className="grid gap-3 rounded-[28px] border-2 border-[#E9A3A0] bg-mal-fondo px-7 py-6 text-sm text-[#6E1414]">
      <h2 className="flex items-center gap-2 text-base font-semibold">
        <OctagonX aria-hidden className="size-5" /> Plan BLOQUEADO: no hay una alternativa segura
      </h2>
      {motivo ? <p><b>Por qué:</b> {motivo}</p> : causas.map((c, i) => <p key={i}><b>Por qué:</b> {c}</p>)}
      {alternativas.length > 0 && (
        <p>
          Se probaron {alternativas.length} alternativas en {rondas} {rondas === 1 ? 'ronda' : 'rondas'} y {fallidas.length === alternativas.length ? 'ninguna' : `solo ${alternativas.length - fallidas.length}`} pasó la verificación con herramientas.
        </p>
      )}
      <p className="flex items-start gap-2 rounded-md bg-white/60 p-2 dark:bg-black/20">
        <Megaphone aria-hidden className="mt-0.5 size-4 shrink-0" />
        <span><b>Escalamiento sugerido:</b> {escalamiento ?? 'Avisar al responsable del área antes de reprogramar la tarea.'}</span>
      </p>
      <p className="text-xs">No se debe iniciar la tarea. Solo se puede rechazar el plan, con un comentario.</p>
    </section>
  )
}
