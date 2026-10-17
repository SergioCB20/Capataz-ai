// Pantalla de inicio (RF-F1-30): presets E1/E2/E2c/E3 que rellenan el formulario, modo libre
// y selector vivo/replay. «Escenario 1» + «Evaluar» = dos clics.
import { useState } from 'react'
import { Loader2, Play } from 'lucide-react'
import type { Catalogo, ModoRun, Tarea } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Textarea } from '@/components/ui/textarea'
import type { PeticionRun } from '@/hooks/useRun'
import { cn } from '@/lib/utils'
import { EstadoSistemaBadge, InsigniaSimulado } from './insignias'

const campo = 'h-9 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'

const tareaVacia = (catalogo: Catalogo): Tarea => ({
  id: `t-libre-${Date.now()}`,
  tipo_tarea: catalogo.tipos_tarea[0]?.id ?? '',
  descripcion: '',
  zona: '',
  turno: { fecha: new Date().toISOString().slice(0, 10), turno: 'dia' },
  asignacion: { personas: [], equipos: [] },
})

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
    setEscenarioId(null) // al editar a mano pasa a modo libre
    setTarea((t) => ({ ...t, ...cambio }))
  }

  const sinEscenarioEnReplay = modo === 'replay' && !escenarioId
  const incompleta = !tarea.descripcion.trim() || !tarea.zona.trim() || !tarea.tipo_tarea
  const nombreTipo = (id: string) => catalogo.tipos_tarea.find((t) => t.id === id)?.nombre ?? id

  return (
    <div className="mx-auto grid max-w-5xl gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Evaluar una tarea antes de ejecutarla</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          CAPATAZ verifica que los controles críticos se puedan ejecutar (personal, equipo y condiciones de campo) y
          entrega un <b>Plan (PTW borrador)</b>. La persona responsable siempre decide.
        </p>
      </div>

      <section aria-labelledby="titulo-escenarios">
        <h2 id="titulo-escenarios" className="mb-2 text-sm font-medium text-muted-foreground">Escenarios de demostración</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {catalogo.escenarios.map((esc) => (
            <button
              key={esc.id}
              type="button"
              onClick={() => elegirPreset(esc.id)}
              aria-pressed={escenarioId === esc.id}
              className={cn(
                'rounded-xl border bg-card p-4 text-left transition hover:border-foreground/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                escenarioId === esc.id && 'border-primary ring-2 ring-primary/30',
              )}
            >
              <div className="text-xs font-medium text-muted-foreground">
                {esc.id === 'E1' ? 'Escenario 1' : `Escenario ${esc.id.slice(1)}`}
              </div>
              <div className="mt-1 font-medium">{esc.nombre}</div>
              <div className="mt-2 flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
                Esperado: <EstadoSistemaBadge estado={esc.resultado_esperado} />
              </div>
            </button>
          ))}
        </div>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>{escenarioId ? `Tarea del escenario ${escenarioId}` : 'Tarea libre'}</CardTitle>
          <CardDescription className="flex flex-wrap items-center gap-2">
            {conBackend ? 'Catálogo cargado desde el servidor.' : 'Sin servidor: catálogo de demostración local.'}
            <InsigniaSimulado />
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="grid gap-4 sm:grid-cols-2"
            onSubmit={(ev) => {
              ev.preventDefault()
              if (!incompleta && !sinEscenarioEnReplay) onIniciar({ modo, escenarioId, tarea })
            }}
          >
            <label className="grid gap-1 text-sm">
              Tipo de tarea
              <select className={campo} value={tarea.tipo_tarea} onChange={(e) => editar({ tipo_tarea: e.target.value })}>
                {catalogo.tipos_tarea.map((t) => (
                  <option key={t.id} value={t.id}>{nombreTipo(t.id)}</option>
                ))}
              </select>
            </label>
            <label className="grid gap-1 text-sm">
              Zona
              <input className={campo} value={tarea.zona} placeholder="Nivel 3200 · Labor 12" onChange={(e) => editar({ zona: e.target.value })} />
            </label>
            <label className="grid gap-1 text-sm sm:col-span-2">
              Descripción
              <Textarea value={tarea.descripcion} placeholder="Qué se va a hacer y en qué condiciones" onChange={(e) => editar({ descripcion: e.target.value })} />
            </label>
            <label className="grid gap-1 text-sm">
              Fecha
              <input type="date" className={campo} value={tarea.turno.fecha} onChange={(e) => editar({ turno: { ...tarea.turno, fecha: e.target.value } })} />
            </label>
            <label className="grid gap-1 text-sm">
              Turno
              <select className={campo} value={tarea.turno.turno} onChange={(e) => editar({ turno: { ...tarea.turno, turno: e.target.value as 'dia' | 'noche' } })}>
                <option value="dia">Día</option>
                <option value="noche">Noche</option>
              </select>
            </label>
            {tarea.asignacion.personas.length + tarea.asignacion.equipos.length > 0 && (
              <p className="text-xs text-muted-foreground sm:col-span-2">
                Asignación propuesta: {tarea.asignacion.personas.join(', ') || 'sin personas'} · {tarea.asignacion.equipos.join(', ') || 'sin equipos'}
              </p>
            )}

            <fieldset className="grid gap-2 sm:col-span-2">
              <legend className="mb-1 text-sm">Modo</legend>
              <RadioGroup value={modo} onValueChange={(v) => setModo(v as ModoRun)} className="flex flex-wrap gap-6">
                <label className="flex items-center gap-2 text-sm">
                  <RadioGroupItem value="vivo" /> En vivo (agentes reales)
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <RadioGroupItem value="replay" /> Replay (corrida grabada, sin red)
                </label>
              </RadioGroup>
              {sinEscenarioEnReplay && <p className="text-xs text-amber-700 dark:text-amber-300">El replay necesita un escenario: elige uno arriba.</p>}
              {modo === 'vivo' && !conBackend && <p className="text-xs text-amber-700 dark:text-amber-300">El servidor no responde: el modo en vivo fallará. Usa replay.</p>}
            </fieldset>

            {error && (
              <p role="alert" className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800 sm:col-span-2 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
                {error}
              </p>
            )}

            <div className="sm:col-span-2">
              <Button type="submit" size="lg" disabled={iniciando || incompleta || sinEscenarioEnReplay}>
                {iniciando ? <Loader2 className="animate-spin" aria-hidden /> : <Play aria-hidden />}
                Evaluar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
