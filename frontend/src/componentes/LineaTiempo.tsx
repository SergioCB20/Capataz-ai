// Línea de tiempo de auditoría (RF-F2-34): eventos clave con actor y hora; el último, resaltado.
import { motion } from 'motion/react'
import type { EntradaLineaTiempo } from '@/eventos/reductor'
import { cn } from '@/lib/utils'
import { nombreActor } from './insignias'

const hora = (ts: string) => new Date(ts).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

const PUNTO: Partial<Record<EntradaLineaTiempo['tipo'], string>> = {
  'conflicto.detectado': 'bg-mal',
  'plan.listo': 'bg-ok',
  'humano.campo_confirmado': 'bg-aviso',
  'humano.decision_tomada': 'bg-acento',
  'run.error': 'bg-mal',
}

export function LineaTiempo({ entradas }: { entradas: EntradaLineaTiempo[] }) {
  return (
    <section aria-labelledby="lt" className="min-w-0 flex-[1_1_320px] rounded-[28px] bg-white px-6 py-6 sm:px-7">
      <h2 id="lt" className="mb-3.5 text-lg font-extrabold">Línea de tiempo</h2>
      {entradas.length === 0 ? (
        <p className="text-sm text-tenue">Aún no hay eventos.</p>
      ) : (
        <ol className="m-0 flex max-h-[420px] list-none flex-col gap-3 overflow-y-auto p-0 pr-1">
          {entradas.map((e, i) => (
            <motion.li
              key={e.seq}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              className="grid grid-cols-[64px_10px_minmax(0,1fr)] items-start gap-2.5 text-[13px] leading-snug"
            >
              <time dateTime={e.ts} className="font-mono text-xs text-tenue">{hora(e.ts)}</time>
              <span aria-hidden className={cn('mt-1.5 size-2.5 rounded-full', PUNTO[e.tipo] ?? 'bg-[#C9C4D9]')} />
              <span className={i === entradas.length - 1 ? 'font-extrabold' : 'font-medium'}>
                {e.texto}
                <span className="block text-xs font-medium text-tenue">#{e.seq} · {nombreActor(e.actor)}</span>
              </span>
            </motion.li>
          ))}
        </ol>
      )}
    </section>
  )
}
