// Insignias de estado: SIEMPRE icono + texto, nunca solo color (RF-F1-32, RF-F3-13).
import { motion } from 'motion/react'
import { CircleCheck, CircleHelp, CircleX, FlaskConical, Loader2, Play, type LucideIcon } from 'lucide-react'
import type { EstadoControl, EstadoSistema, Fuente } from '@/api/types'
import { cn } from '@/lib/utils'

type Tono = 'ok' | 'aviso' | 'peligro' | 'neutro'

const TONOS: Record<Tono, string> = {
  ok: 'bg-ok-fondo text-ok',
  aviso: 'bg-aviso-fondo text-aviso',
  peligro: 'bg-mal-fondo text-mal',
  neutro: 'bg-segmento text-tinta-2',
}

export function Pastilla({ tono, icono: Icono, texto, girar, className }: {
  tono: Tono; icono: LucideIcon; texto: string; girar?: boolean; className?: string
}) {
  return (
    <motion.span
      key={texto}
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-extrabold whitespace-nowrap', TONOS[tono], className)}
    >
      <Icono aria-hidden className={cn('size-3.5', girar && 'animate-spin')} />
      {texto}
    </motion.span>
  )
}

const CONTROL: Record<EstadoControl, { tono: Tono; icono: LucideIcon }> = {
  CUMPLE: { tono: 'ok', icono: CircleCheck },
  NO_VERIFICABLE: { tono: 'aviso', icono: CircleHelp },
  NO_CUMPLE: { tono: 'peligro', icono: CircleX },
}

/** Estado de un control o requisito; `null` = todavía en verificación (nunca se muestra como CUMPLE). */
export function EstadoControlBadge({ estado }: { estado: EstadoControl | null }) {
  if (!estado) return <Pastilla tono="neutro" icono={Loader2} girar texto="En verificación" />
  const { tono, icono } = CONTROL[estado]
  return <Pastilla tono={tono} icono={icono} texto={estado} />
}

const SISTEMA: Record<EstadoSistema, { tono: Tono; icono: LucideIcon }> = {
  RECOMENDADO: { tono: 'ok', icono: CircleCheck },
  REQUIERE_CAMPO: { tono: 'aviso', icono: CircleHelp },
  BLOQUEADO: { tono: 'peligro', icono: CircleX },
}

export function EstadoSistemaBadge({ estado }: { estado: EstadoSistema | null }) {
  if (!estado) return <Pastilla tono="neutro" icono={Loader2} girar texto="Evaluando" />
  const { tono, icono } = SISTEMA[estado]
  return <Pastilla tono={tono} icono={icono} texto={estado} />
}

/** Insignia «simulado» para todo dato con `Fuente.tipo == simulado` (RT-07). */
export function InsigniaSimulado({ fuente, className }: { fuente?: Pick<Fuente, 'tipo'> | null; className?: string }) {
  if (fuente && fuente.tipo !== 'simulado') return null
  return <Pastilla tono="neutro" icono={FlaskConical} texto="simulado" className={className} />
}

export function InsigniaReplay() {
  return <Pastilla tono="neutro" icono={Play} texto="Replay" />
}

export const NOMBRE_AGENTE: Record<string, string> = {
  supervisor: 'Supervisor',
  riesgo: 'Agente Riesgo',
  personal: 'Agente Personal',
  equipo: 'Agente Equipo',
}

/** `capataz:agente-personal` => «Agente Personal»; `humano:x` => «x». */
export function nombreActor(actor: string): string {
  const corto = actor.replace(/^capataz:agente-/, '')
  if (NOMBRE_AGENTE[corto]) return NOMBRE_AGENTE[corto]
  if (actor.startsWith('humano:')) return actor.slice('humano:'.length)
  return actor === 'sistema' ? 'Sistema' : actor
}
