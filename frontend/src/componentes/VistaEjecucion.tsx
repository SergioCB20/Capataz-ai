// Vista de ejecución: grafo, semáforo, evidencia y decisión, todo derivado del reductor.
import { useMemo, useState } from 'react'
import { Activity, ArrowLeft, CircleAlert, Loader2, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import type { Catalogo } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { EstadoConexion } from '@/eventos/fuentes'
import { filasControles, incidentesDeControl, nombrePeligro, type FilaControl, type FilaRequisito } from '@/eventos/vista'
import type { ControlRun } from '@/hooks/useRun'
import { BarraDecision } from './BarraDecision'
import { CajonEvidencia } from './CajonEvidencia'
import { GrafoAgentes } from './GrafoAgentes'
import { InsigniaReplay, Pastilla } from './insignias'
import { Semaforo } from './Semaforo'

const CONEXION: Record<EstadoConexion, { texto: string; tono: 'ok' | 'aviso' | 'peligro' | 'neutro' }> = {
  conectando: { texto: 'Conectando', tono: 'neutro' },
  abierta: { texto: 'En vivo', tono: 'ok' },
  reconectando: { texto: 'Reconectando', tono: 'aviso' },
  cerrada: { texto: 'Stream cerrado', tono: 'neutro' },
  error: { texto: 'Sin conexión', tono: 'peligro' },
}

export function VistaEjecucion({ run, catalogo }: { run: ControlRun; catalogo: Catalogo }) {
  const { estado, sesion, conexion } = run
  const [seleccion, setSeleccion] = useState<{ control: FilaControl; requisito: FilaRequisito } | null>(null)
  const filas = useMemo(() => filasControles(estado, catalogo), [estado, catalogo])
  const sinEventos = estado.ultimoSeq === 0
  const c = CONEXION[conexion]

  return (
    <div className="mx-auto grid max-w-7xl gap-4 p-4 sm:p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <Button variant="ghost" size="sm" onClick={run.salir}>
            <ArrowLeft aria-hidden /> Nueva tarea
          </Button>
          <div className="min-w-0">
            <h1 className="truncate font-semibold">{estado.tarea?.descripcion ?? 'Evaluación en curso'}</h1>
            {estado.tarea && (
              <p className="text-xs text-muted-foreground">
                {estado.tarea.zona} · turno {estado.tarea.turno.turno === 'dia' ? 'día' : 'noche'} del {estado.tarea.turno.fecha}
              </p>
            )}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {sesion?.modo === 'replay' && <InsigniaReplay />}
          {sesion?.origen === 'local' && <Pastilla tono="neutro" icono={WifiOff} texto="Sin backend" />}
          {sesion?.origen === 'backend' && (
            <Pastilla tono={c.tono} icono={conexion === 'reconectando' ? RefreshCw : Wifi} girar={conexion === 'reconectando'} texto={c.texto} />
          )}
          {estado.estadoRun && (
            <Pastilla
              tono="neutro"
              {...(['EVALUANDO', 'RESOLVIENDO_CONFLICTO'].includes(estado.estadoRun) ? { icono: Loader2, girar: true } : { icono: Activity })}
              texto={estado.estadoRun}
            />
          )}
        </div>
      </header>

      {estado.error && (
        <div role="alert" className="flex flex-wrap items-center gap-3 rounded-xl border border-red-300 bg-red-50 p-4 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
          <CircleAlert aria-hidden className="size-5" />
          <span className="flex-1">La evaluación falló: {estado.error}. Ningún requisito se dio por cumplido.</span>
          <Button variant="outline" size="sm" onClick={run.salir}>Volver al inicio</Button>
        </div>
      )}

      {sinEventos && !estado.error ? (
        <div className="flex items-center justify-center gap-2 rounded-xl border p-12 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" aria-hidden />
          {conexion === 'reconectando' ? 'Reconectando con el backend…' : 'Esperando los primeros eventos…'}
        </div>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
            <Card>
              <CardHeader>
                <CardTitle>Agentes</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3">
                <GrafoAgentes agentes={estado.agentes} />
                {estado.evaluacion && (
                  <div className="grid gap-2 text-sm">
                    <h3 className="font-medium">Peligros detectados por el Agente Riesgo</h3>
                    <ul className="grid gap-2">
                      {estado.evaluacion.peligros.map((p) => (
                        <li key={p.peligro_id} className="rounded-md border p-2">
                          <b>{nombrePeligro(catalogo, p.peligro_id)}</b>
                          <p className="text-muted-foreground">{p.justificacion}</p>
                          {p.incidentes_similares.length > 0 && (
                            <p className="mt-1 text-xs text-muted-foreground">Incidentes similares: {p.incidentes_similares.join(', ')} (simulados)</p>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Controles críticos</CardTitle>
              </CardHeader>
              <CardContent>
                <Semaforo
                  filas={filas}
                  nombrePeligro={(id) => nombrePeligro(catalogo, id)}
                  onElegir={(control, requisito) => setSeleccion({ control, requisito })}
                />
              </CardContent>
            </Card>
          </div>

          <BarraDecision
            estadoSistema={estado.estadoSistema}
            estadoRun={estado.estadoRun}
            requerida={estado.decisionRequerida}
            decision={estado.decision}
            enviando={run.enviando}
            error={run.errorAccion}
            onDecidir={run.decidir}
          />
        </>
      )}

      <CajonEvidencia
        seleccion={seleccion}
        incidentes={seleccion ? incidentesDeControl(estado, catalogo, seleccion.control.controlId) : []}
        onCerrar={() => setSeleccion(null)}
      />
    </div>
  )
}
