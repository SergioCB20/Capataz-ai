// Menú lateral: navegación entre «Nueva evaluación» y la ejecución en curso, y el recordatorio
// de que la persona decide (el plan es un PTW borrador).
import { CirclePlay, Plus } from 'lucide-react'
import logo from '@/assets/logo-capataz.png'
import { cn } from '@/lib/utils'

export type Pantalla = 'inicio' | 'ejecucion'

function Logo() {
  return (
    <div className="flex items-center gap-3 px-2">
      <img src={logo} alt="" aria-hidden="true" width={40} height={40} className="size-10" />
      <span className="text-xl font-extrabold tracking-tight">CAPATAZ</span>
    </div>
  )
}

function Item({ activo, deshabilitado, onClick, icono, children, ayuda }: {
  activo: boolean
  deshabilitado?: boolean
  onClick: () => void
  icono: React.ReactNode
  children: React.ReactNode
  ayuda?: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={deshabilitado}
      aria-current={activo ? 'page' : undefined}
      title={ayuda}
      className={cn(
        'flex min-h-12 w-full items-center gap-3 rounded-full px-4 text-left font-semibold transition-colors focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-acento',
        activo ? 'bg-tinta text-white' : 'text-tinta hover:bg-segmento',
        deshabilitado && 'cursor-not-allowed text-tenue hover:bg-transparent',
      )}
    >
      {icono}
      {children}
    </button>
  )
}

export function MenuLateral({ pantalla, hayEjecucion, onIr }: {
  pantalla: Pantalla
  hayEjecucion: boolean
  onIr: (p: Pantalla) => void
}) {
  return (
    <nav aria-label="Menú principal" className="flex min-w-0 flex-[1_1_240px] flex-col gap-7 rounded-[28px] bg-white px-4 py-6 lg:max-w-[280px]">
      <Logo />
      <div className="flex flex-col gap-1.5">
        <Item activo={pantalla === 'inicio'} onClick={() => onIr('inicio')} icono={<Plus aria-hidden className="size-5" />}>
          Nueva evaluación
        </Item>
        <Item
          activo={pantalla === 'ejecucion'}
          deshabilitado={!hayEjecucion}
          ayuda={hayEjecucion ? undefined : 'Aún no hay una evaluación en curso'}
          onClick={() => onIr('ejecucion')}
          icono={<CirclePlay aria-hidden className="size-5" />}
        >
          Ejecución en curso
        </Item>
      </div>
      <div className="mt-auto flex flex-col gap-2 rounded-[22px] bg-acento-suave p-4">
        <div className="text-base font-extrabold">Tú decides</div>
        <p className="m-0 text-[13px] leading-relaxed text-tinta-2">
          CAPATAZ entrega un <b>Plan (PTW borrador)</b>. No firma ni autoriza: la persona responsable aprueba o rechaza.
        </p>
        <span className="self-start rounded-full bg-white px-2.5 py-1 text-xs font-bold text-acento-texto">Datos simulados</span>
      </div>
    </nav>
  )
}
