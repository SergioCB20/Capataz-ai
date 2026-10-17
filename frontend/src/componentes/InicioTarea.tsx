// Pantalla de inicio (RF-F1-30): cómo funciona, presets E1/E2/E2c/E3 que rellenan el formulario,
// modo libre y selector en vivo / replay. «Escenario» + «Evaluar tarea» = dos clics.
import { useState } from 'react'
import { ArrowRight, CircleCheck, Loader2 } from 'lucide-react'
import type { Catalogo, EstadoSistema, ModoRun, Tarea } from '@/api/types'
import type { PeticionRun } from '@/hooks/useRun'
import { cn } from '@/lib/utils'

const campo =
  'h-12 w-full rounded-[14px] border-[1.5px] border-[#DCD8E8] bg-campo px-3.5 text-[15px] font-medium text-tinta focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-acento'

const tarjeta = 'rounded-[28px] bg-white px-6 py-6 sm:px-8'

const PILL_ESPERADO: Record<EstadoSistema, string> = {
  RECOMENDADO: 'bg-ok-fondo text-ok',
  REQUIERE_CAMPO: 'bg-aviso-fondo text-aviso',
  BLOQUEADO: 'bg-mal-fondo text-mal',
}

const PASOS = [
  { n: 1, titulo: 'Describe la tarea', texto: 'Tipo, zona y turno.' },
  { n: 2, titulo: 'Los agentes verifican', texto: 'Riesgo, personal y equipo.' },
  { n: 3, titulo: 'Si algo falla, alternativas', texto: 'Cada una re-verificada con herramientas.' },
  { n: 4, titulo: 'Tú decides', texto: 'Aprobar o rechazar el plan.' },
]

const tareaVacia = (catalogo: Catalogo): Tarea => ({
  id: `t-libre-${Date.now()}`,
  tipo_tarea: catalogo.tipos_tarea[0]?.id ?? '',
  descripcion: '',
  zona: '',
  turno: { fecha: new Date().toISOString().slice(0, 10), turno: 'dia' },
  asignacion: { personas: [], equipos: [] },
})

function Segmentado<T extends string>({ valor, opciones, onCambio, redondo, etiqueta }: {
  valor: T
  opciones: { valor: T; texto: string }[]
  onCambio: (v: T) => void
  redondo?: boolean
  etiqueta: string
}) {
  return (
    <div role="group" aria-label={etiqueta} className={cn('grid grid-cols-2 gap-1 bg-segmento p-1', redondo ? 'rounded-full' : 'rounded-[14px]')}>
      {opciones.map((o) => (
        <button
          key={o.valor}
          type="button"
          aria-pressed={valor === o.valor}
          onClick={() => onCambio(o.valor)}
          className={cn(
            'min-h-11 px-4 text-sm font-bold transition-colors focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-acento',
            redondo ? 'rounded-full' : 'rounded-[10px]',
            valor === o.valor ? 'bg-tinta text-white' : 'text-tinta-2 hover:bg-white',
          )}
        >
          {o.texto}
        </button>
      ))}
    </div>
  )
}

export function InicioTarea({ catalogo, conBackend, iniciando, error, onIniciar }: {
  catalogo: Catalogo
  conBackend: boolean
  iniciando: boolean
  error: string | null
  onIniciar: (p: PeticionRun) => void
}) {
  const [escenarioId, setEscenarioId] = useState<string | null>(null)
  const [tarea, setTarea] = useState<Tarea>(() => tareaVacia(catalogo))
  const [modo, setModo] = useState<ModoRun>(conBackend ? 'vivo' : 'replay')

  const elegirPreset = (id: string) => {
    const esc = catalogo.escenarios.find((e) => e.id === id)
    if (!esc) return
    setEscenarioId(id)
    setTarea(structuredClone(esc.tarea))
  }
  const editar = (cambio: Partial<Tarea>) => {
    setEscenarioId(null) // editar a mano pasa a tarea libre
    setTarea((t) => ({ ...t, ...cambio }))
  }

  const faltan = [!tarea.zona.trim() && 'la zona', !tarea.descripcion.trim() && 'la descripción'].filter(Boolean)
  const faltante = faltan.length
    ? `Falta ${faltan.join(' y ')}.`
    : modo === 'replay' && !escenarioId
      ? 'El replay necesita un escenario: elige uno arriba.'
      : null
  const [, m, d] = tarea.turno.fecha.split('-')

  return (
    <>
      <header className={cn(tarjeta, 'flex flex-wrap items-center justify-between gap-6')}>
        <div className="min-w-0">
          <h1 className="m-0 text-[34px] font-extrabold tracking-tight">Nueva evaluación</h1>
          <p className="mt-1.5 text-[15px] text-tenue">Antes de ejecutar la tarea, verifica que sus controles críticos se pueden cumplir de verdad.</p>
        </div>
        <div className="min-w-60 rounded-[22px] bg-acento-suave px-5 py-4">
          <div className="text-[13px] font-semibold text-acento-texto">Turno seleccionado</div>
          <div className="mt-0.5 text-[26px] font-extrabold tracking-tight">
            {tarea.turno.turno === 'dia' ? 'Día' : 'Noche'} · {d}/{m}
          </div>
        </div>
      </header>

      <section aria-labelledby="como" className={tarjeta}>
        <h2 id="como" className="mb-4 text-lg font-extrabold">Cómo funciona</h2>
        <ol className="m-0 grid list-none grid-cols-[repeat(auto-fit,minmax(190px,1fr))] gap-4 p-0">
          {PASOS.map((p) => (
            <li key={p.n} className="flex items-start gap-3">
              <span className={cn('grid size-8 flex-none place-items-center rounded-full text-sm font-extrabold text-white', p.n === 4 ? 'bg-acento' : 'bg-tinta')}>{p.n}</span>
              <span className="text-sm leading-snug">
                <b>{p.titulo}</b>
                <br />
                <span className="text-tenue">{p.texto}</span>
              </span>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="esc" className={tarjeta}>
        <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="esc" className="text-lg font-extrabold">Empieza con un escenario</h2>
          <span className="text-[13px] text-tenue">Rellena el formulario por ti · o escribe una tarea libre abajo</span>
        </div>
        <div className="grid grid-cols-[repeat(auto-fit,minmax(210px,1fr))] gap-3.5">
          {catalogo.escenarios.map((esc) => {
            const sel = escenarioId === esc.id
            return (
              <button
                key={esc.id}
                type="button"
                onClick={() => elegirPreset(esc.id)}
                aria-pressed={sel}
                className={cn(
                  'flex min-h-48 flex-col items-start gap-2.5 rounded-[22px] border-2 p-[18px] text-left transition-colors focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-acento',
                  sel ? 'border-acento bg-acento-fondo' : 'border-transparent bg-campo hover:border-[#DCD8E8]',
                )}
              >
                <span className="flex w-full items-center justify-between">
                  <span className="font-mono text-[13px] text-tenue">{esc.id}</span>
                  {sel && <CircleCheck aria-hidden className="size-6 fill-acento text-white" />}
                </span>
                <span className="text-[17px] leading-tight font-extrabold">{esc.nombre}</span>
                <span className="line-clamp-3 text-[13px] leading-snug text-tenue">{esc.tarea.descripcion}</span>
                <span className={cn('mt-auto rounded-full px-2.5 py-1 text-xs font-bold', PILL_ESPERADO[esc.resultado_esperado])}>
                  Esperado: {esc.resultado_esperado}
                </span>
              </button>
            )
          })}
        </div>
      </section>

      <section aria-labelledby="form" className={tarjeta}>
        <h2 id="form" className="text-lg font-extrabold">{escenarioId ? `Tarea del escenario ${escenarioId}` : 'Tarea libre'}</h2>
        <p className="mt-1 mb-[18px] text-[13px] text-tenue">
          {conBackend ? 'Catálogo cargado desde el servidor.' : 'Sin servidor: catálogo empaquetado en la app.'} Los datos de personal, equipos e incidentes son simulados.
        </p>
        <form
          onSubmit={(ev) => {
            ev.preventDefault()
            if (!faltante) onIniciar({ modo, escenarioId, tarea })
          }}
        >
          <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
            <label className="flex flex-col gap-1.5 text-[13px] font-bold">
              Tipo de tarea
              <select className={campo} value={tarea.tipo_tarea} onChange={(e) => editar({ tipo_tarea: e.target.value })}>
                {catalogo.tipos_tarea.map((t) => (
                  <option key={t.id} value={t.id}>{t.nombre || t.id}</option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1.5 text-[13px] font-bold">
              Zona
              <input className={campo} value={tarea.zona} placeholder="Nivel 3200 · Labor 12" onChange={(e) => editar({ zona: e.target.value })} />
            </label>
            <label className="flex flex-col gap-1.5 text-[13px] font-bold">
              Fecha
              <input type="date" className={campo} value={tarea.turno.fecha} onChange={(e) => editar({ turno: { ...tarea.turno, fecha: e.target.value } })} />
            </label>
            <div className="flex flex-col gap-1.5 text-[13px] font-bold">
              <span id="turno-lbl">Turno</span>
              <Segmentado
                etiqueta="Turno"
                valor={tarea.turno.turno}
                opciones={[{ valor: 'dia', texto: 'Día' }, { valor: 'noche', texto: 'Noche' }]}
                onCambio={(v) => editar({ turno: { ...tarea.turno, turno: v } })}
              />
            </div>
            <label className="col-span-full flex flex-col gap-1.5 text-[13px] font-bold">
              Descripción
              <textarea
                rows={3}
                value={tarea.descripcion}
                placeholder="Qué se va a hacer y en qué condiciones"
                onChange={(e) => editar({ descripcion: e.target.value })}
                className={cn(campo, 'h-auto resize-y py-3')}
              />
            </label>
          </div>

          {tarea.asignacion.personas.length + tarea.asignacion.equipos.length > 0 && (
            <p className="mt-3 text-xs text-tenue">
              Asignación propuesta: {tarea.asignacion.personas.join(', ') || 'sin personas'} · {tarea.asignacion.equipos.join(', ') || 'sin equipos'}
            </p>
          )}

          <div className="mt-5 flex flex-wrap items-center justify-between gap-5 border-t border-linea pt-5">
            <div className="flex flex-wrap items-center gap-3">
              <div className="min-w-[300px]">
                <Segmentado
                  etiqueta="Modo de ejecución"
                  redondo
                  valor={modo}
                  opciones={[{ valor: 'vivo', texto: 'En vivo' }, { valor: 'replay', texto: 'Replay (sin red)' }]}
                  onCambio={setModo}
                />
              </div>
              <span className="max-w-[340px] text-[13px] text-tenue">
                {modo === 'vivo'
                  ? conBackend
                    ? 'Los agentes trabajan ahora contra el servidor local.'
                    : 'El servidor no responde: el modo en vivo fallará. Usa replay.'
                  : 'Reproduce una corrida grabada. Funciona sin Internet.'}
              </span>
            </div>
            <div className="flex flex-col items-end gap-1.5">
              <button
                type="submit"
                disabled={iniciando || !!faltante}
                className="inline-flex min-h-14 items-center gap-2.5 rounded-full bg-acento px-7 text-base font-extrabold text-white transition-opacity hover:opacity-90 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-acento disabled:bg-[#D9D5E6] disabled:text-[#4A4659]"
              >
                {iniciando ? <Loader2 aria-hidden className="size-5 animate-spin" /> : null}
                Evaluar tarea
                {!iniciando && <ArrowRight aria-hidden className="size-5" />}
              </button>
              {faltante && <span className="text-[13px] font-semibold text-[#8A2B12]">{faltante}</span>}
            </div>
          </div>

          {error && (
            <p role="alert" className="mt-4 rounded-2xl bg-mal-fondo p-3 text-sm font-semibold text-mal">
              {error}
            </p>
          )}
        </form>
      </section>
    </>
  )
}
