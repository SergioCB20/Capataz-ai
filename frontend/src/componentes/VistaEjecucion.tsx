// Vista de ejecución: grafo, semáforo, evidencia y decisión, todo derivado del reductor.
import { useMemo, useState } from 'react'
import { Activity, ArrowLeft, CircleAlert, Loader2, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import type { Catalogo } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { EstadoConexion } from '@/eventos/fuentes'
import { candidatos, sinAlternativaSegura } from '@/eventos/reductor'
import { filasControles, incidentesDeControl, nombrePeligro, nombreRecurso, type FilaControl, type FilaRequisito } from '@/eventos/vista'
import type { ControlRun } from '@/hooks/useRun'
import { BarraDecision } from './BarraDecision'
import { CajonEvidencia } from './CajonEvidencia'
import { ComparacionPlanes } from './ComparacionPlanes'
import { EstadoBloqueado } from './EstadoBloqueado'
import { FormCampo } from './FormCampo'
import { GrafoAgentes } from './GrafoAgentes'
import { InsigniaReplay, Pastilla } from './insignias'
import { LineaTiempo } from './LineaTiempo'
import { Semaforo } from './Semaforo'
import { VistaConflicto } from './VistaConflicto'

const CONEXION: Record<EstadoConexion, { texto: string; tono: 'ok' | 'aviso' | 'peligro' | 'neutro' }> = {
  conectando: { texto: 'Conectando', tono: 'neutro' },
  abierta: { texto: 'En vivo', tono: 'ok' },
  reconectando: { texto: 'Reconectando', tono: 'aviso' },
  cerrada: { texto: 'Conexión cerrada', tono: 'neutro' },
  error: { texto: 'Sin conexión', tono: 'peligro' },
}

/** Descarga eventos + decisión como JSON (RF-F3-30). Se genera en el navegador; no se envía a ningún lado. */
function exportarAuditoria({ estado, eventos, sesion }: ControlRun) {
  const datos = {
    run_id: estado.runId,
    modo: sesion?.modo,
    origen: sesion?.origen,
    exportado_en: new Date().toISOString(),
    tarea: estado.tarea,
    estado_run: estado.estadoRun,
    plan: estado.plan,
    decision: estado.decision,
    nota: 'Datos simulados (hackatón). El plan es un PTW borrador; la persona responsable decide.',
    eventos,
  }
  const url = URL.createObjectURL(new Blob([JSON.stringify(datos, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `auditoria-${estado.runId ?? 'run'}.json`
  a.click()
  URL.revokeObjectURL(url)
}

export function VistaEjecucion({ run, catalogo }: { run: ControlRun; catalogo: Catalogo }) {
  const { estado, sesion, conexion } = run
  const [seleccion, setSeleccion] = useState<{ control: FilaControl; requisito: FilaRequisito } | null>(null)
  const filas = useMemo(() => filasControles(estado, catalogo), [estado, catalogo])
  const sinEventos = estado.ultimoSeq === 0
  const [planElegido, setPlanElegido] = useState<string | null>(null)
  const planes = useMemo(() => candidatos(estado), [estado])
  const planId = planElegido ?? estado.decisionRequerida?.plan_id ?? planes[0]?.id ?? ''
  const planActual = planes.find((p) => p.id === planId) ?? planes[0] ?? null
  const bloqueado = sinAlternativaSegura(estado)
  const nombreControl = (id: string) => catalogo.controles.find((x) => x.id === id)?.nombre ?? id
  const recurso = (v: string) => nombreRecurso(catalogo, v)
  // «Antes» del diff: el plan original de P2 si hay alternativas; si no, la asignación de la tarea.
  const original = estado.planesAlternativos.length && estado.plan ? estado.plan.asignacion : estado.tarea?.asignacion
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
          {sesion?.origen === 'local' && <Pastilla tono="neutro" icono={WifiOff} texto="Replay local (sin servidor)" />}
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
          {conexion === 'reconectando' ? 'Reconectando con el servidor…' : 'Esperando los primeros eventos…'}
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

          {estado.conflictos.length > 0 && (
            <VistaConflicto
              conflictos={estado.conflictos}
              nombreControl={nombreControl}
              nombreRecurso={recurso}
              ronda={estado.ronda}
              alternativas={estado.alternativas}
              enCurso={estado.estadoRun === 'RESOLVIENDO_CONFLICTO'}
            />
          )}

          {estado.estadoRun === 'ESPERANDO_CAMPO' && estado.preguntasCampo.length > 0 && (
            <FormCampo preguntas={estado.preguntasCampo} enviando={run.enviando} error={run.errorAccion} onEnviar={run.confirmarCampo} />
          )}

          {bloqueado && (
            <EstadoBloqueado
              motivo={estado.plan?.motivo}
              causas={estado.conflictos.map((c) => c.causa)}
              alternativas={estado.alternativas}
              escalamiento={estado.plan?.escalamiento}
            />
          )}

          {original && planes.length > 0 && !bloqueado && (estado.planesAlternativos.length > 0 || planes[0].cambios.length > 0) && (
            <ComparacionPlanes
              original={original}
              planes={planes}
              alternativas={estado.alternativas}
              nombreRecurso={recurso}
              elegido={planId}
              onElegir={setPlanElegido}
              catalogo={catalogo}
              puedeElegir={!!estado.decisionRequerida}
            />
          )}

          <BarraDecision
            estadoSistema={planActual?.estado_sistema ?? estado.estadoSistema}
            estadoRun={estado.estadoRun}
            requerida={estado.decisionRequerida}
            decision={estado.decision}
            planElegido={planes.length > 1 ? planId : null}
            enviando={run.enviando}
            error={estado.estadoRun === 'ESPERANDO_CAMPO' ? null : run.errorAccion}
            onDecidir={(d, comentario) => run.decidir(d, comentario, planId || undefined)}
          />

          <LineaTiempo entradas={estado.lineaTiempo} onExportar={() => exportarAuditoria(run)} />
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
