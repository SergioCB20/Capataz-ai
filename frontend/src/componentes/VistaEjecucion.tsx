// Vista de ejecución: progreso, flujo de agentes, controles con evidencia, alternativas y decisión.
// Todo se deriva del reductor de eventos (mismo resultado en vivo y en replay).
import { useMemo, useState } from 'react'
import { Activity, ArrowLeft, CircleAlert, Loader2, Play, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import type { Catalogo } from '@/api/types'
import type { EstadoConexion } from '@/eventos/fuentes'
import { candidatos, claveRequisito, sinAlternativaSegura } from '@/eventos/reductor'
import { filasControles, filasDePlan, incidentesDeControl, nombreRecurso } from '@/eventos/vista'
import type { ControlRun } from '@/hooks/useRun'
import { BarraDecision } from './BarraDecision'
import { ComparacionPlanes } from './ComparacionPlanes'
import { EstadoBloqueado } from './EstadoBloqueado'
import { FormCampo } from './FormCampo'
import { GrafoAgentes } from './GrafoAgentes'
import { EstadoSistemaBadge, Pastilla } from './insignias'
import { LineaTiempo } from './LineaTiempo'
import { PanelEvidencia } from './PanelEvidencia'
import { ProgresoEvaluacion } from './ProgresoEvaluacion'
import { TablaControles, type VistaPlan } from './TablaControles'
import { TIPO_CAMBIO, VistaConflicto } from './VistaConflicto'

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

export function VistaEjecucion({ run, catalogo, onNuevaTarea }: { run: ControlRun; catalogo: Catalogo; onNuevaTarea: () => void }) {
  const { estado, sesion, conexion } = run
  const [planElegido, setPlanElegido] = useState<string | null>(null)
  const [vista, setVista] = useState<VistaPlan>('elegido')
  const [clave, setClave] = useState<string | null>(null)

  const planes = useMemo(() => candidatos(estado), [estado])
  const planId = planElegido ?? estado.decisionRequerida?.plan_id ?? planes[0]?.id ?? null
  const planActual = planes.find((p) => p.id === planId) ?? planes[0] ?? null
  const comparar = !!estado.plan && estado.planesAlternativos.length > 0
  const bloqueado = sinAlternativaSegura(estado)
  const recurso = (v: string) => nombreRecurso(catalogo, v)
  const nombreControl = (id: string) => catalogo.controles.find((x) => x.id === id)?.nombre ?? id

  const filas = useMemo(() => {
    if (!comparar) return filasControles(estado, catalogo)
    const plan = vista === 'original' ? estado.plan! : planActual!
    return filasDePlan(plan.resultados, estado, catalogo)
  }, [comparar, vista, estado, catalogo, planActual])

  // Requisito elegido: el que marcó la persona o, por defecto, el primero que ya tiene resultado.
  const todas = filas.flatMap((c) => c.requisitos.map((r) => ({ control: c, requisito: r })))
  const claveDe = (s: (typeof todas)[number]) => claveRequisito({ control_id: s.control.controlId, requisito_id: s.requisito.requisito.id })
  const seleccion = todas.find((s) => claveDe(s) === clave) ?? todas.find((s) => s.requisito.resultado) ?? todas[0] ?? null

  const resumenPlan = planActual
    ? planActual.cambios.length
      ? planActual.cambios.map((c) => `${TIPO_CAMBIO[c.tipo].toLowerCase()} ${recurso(c.desde)} → ${recurso(c.hacia)}`).join('; ') + '.'
      : 'sin cambios frente a la asignación original.'
    : null

  const ayudaPlan = estado.decision
    ? `${estado.decision.decision === 'aprobar' ? 'Aprobado' : 'Rechazado'} por ${estado.decision.usuario}`
    : estado.estadoRun === 'ESPERANDO_CAMPO'
      ? 'Falta confirmar en campo'
      : estado.decisionRequerida
        ? 'Esperando tu decisión'
        : estado.error
          ? 'La evaluación falló'
          : 'Evaluando…'
  const c = CONEXION[conexion]
  const sinEventos = estado.ultimoSeq === 0
  const enCurso = estado.estadoRun === 'EVALUANDO' || estado.estadoRun === 'RESOLVIENDO_CONFLICTO'

  return (
    <>
      <header className="flex flex-wrap items-center justify-between gap-6 rounded-[28px] bg-white px-6 py-6 sm:px-8">
        <div className="min-w-0 flex-[1_1_420px]">
          <button
            type="button"
            onClick={onNuevaTarea}
            className="inline-flex min-h-8 items-center gap-1.5 text-sm font-bold text-acento-texto hover:text-tinta focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-acento"
          >
            <ArrowLeft aria-hidden className="size-[18px]" /> Nueva tarea
          </button>
          <h1 className="mt-1.5 text-[28px] leading-tight font-extrabold tracking-tight">{estado.tarea?.descripcion ?? 'Evaluación en curso'}</h1>
          <div className="mt-2.5 flex flex-wrap items-center gap-2 text-[13px] text-tenue">
            {estado.tarea && (
              <span>
                {estado.tarea.zona} · turno {estado.tarea.turno.turno === 'dia' ? 'día' : 'noche'} · {estado.tarea.turno.fecha}
              </span>
            )}
            {sesion?.modo === 'replay' && <Pastilla tono="neutro" icono={Play} texto="Replay" />}
            {sesion?.origen === 'local' && <Pastilla tono="neutro" icono={WifiOff} texto="Sin servidor" />}
            {sesion?.origen === 'backend' && (
              <Pastilla tono={c.tono} icono={conexion === 'reconectando' ? RefreshCw : Wifi} girar={conexion === 'reconectando'} texto={c.texto} />
            )}
            {estado.estadoRun && (
              <Pastilla tono="neutro" {...(enCurso ? { icono: Loader2, girar: true } : { icono: Activity })} texto={estado.estadoRun} />
            )}
          </div>
        </div>
        <div className="min-w-[260px] rounded-[22px] bg-acento-suave px-5 py-4">
          <div className="text-[13px] font-bold text-acento-texto">Plan (PTW borrador)</div>
          <div className="mt-1.5 flex items-center gap-2.5">
            <EstadoSistemaBadge estado={planActual?.estado_sistema ?? estado.estadoSistema} />
            {planActual && <span className="font-mono text-sm">{planActual.id}</span>}
          </div>
          <div className="mt-1.5 text-[13px] text-tinta-2">{ayudaPlan}</div>
        </div>
      </header>

      {estado.error && (
        <div role="alert" className="flex flex-wrap items-center gap-3 rounded-[28px] bg-mal-fondo px-6 py-4 text-sm text-[#6E1414]">
          <CircleAlert aria-hidden className="size-5" />
          <span className="flex-1">La evaluación falló: {estado.error}. Ningún requisito se dio por cumplido.</span>
          <button type="button" onClick={onNuevaTarea} className="min-h-11 rounded-full bg-white px-4 font-bold">Volver al inicio</button>
        </div>
      )}

      {sinEventos && !estado.error ? (
        <div className="flex items-center justify-center gap-2 rounded-[28px] bg-white p-12 text-sm text-tenue">
          <Loader2 className="size-4 animate-spin" aria-hidden />
          {conexion === 'reconectando' ? 'Reconectando con el servidor…' : 'Esperando los primeros eventos…'}
        </div>
      ) : (
        <>
          <ProgresoEvaluacion estado={estado} />

          <section aria-labelledby="ag" className="rounded-[28px] bg-white px-6 py-6 sm:px-7">
            <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
              <h2 id="ag" className="text-lg font-extrabold">Agentes</h2>
              <span className="text-[13px] text-tenue">El Supervisor reparte; Personal y Equipo verifican con herramientas deterministas</span>
            </div>
            <GrafoAgentes agentes={estado.agentes} />
          </section>

          <div className="flex flex-wrap items-stretch gap-5">
            <TablaControles
              filas={filas}
              seleccion={seleccion ? claveDe(seleccion) : null}
              onElegir={(control, requisito) => setClave(claveRequisito({ control_id: control.controlId, requisito_id: requisito.requisito.id }))}
              comparar={comparar}
              vista={vista}
              onVista={setVista}
              etiquetaElegido={`Plan elegido (${planActual?.id ?? '—'})`}
            />
            <PanelEvidencia
              seleccion={seleccion}
              incidentes={seleccion ? incidentesDeControl(estado, catalogo, seleccion.control.controlId) : []}
            />
          </div>

          {estado.conflictos.length > 0 && (
            <VistaConflicto
              conflictos={estado.conflictos}
              nombreControl={nombreControl}
              nombreRecurso={recurso}
              ronda={estado.ronda}
              alternativas={estado.alternativas}
              planes={estado.planesAlternativos}
              elegido={comparar ? planActual?.id ?? null : null}
              onElegir={(id) => {
                setPlanElegido(id)
                setVista('elegido')
              }}
              puedeElegir={!!estado.decisionRequerida && !estado.decision}
              enCurso={estado.estadoRun === 'RESOLVIENDO_CONFLICTO'}
            >
              {comparar && planActual && estado.plan && (
                <ComparacionPlanes original={estado.plan.asignacion} plan={planActual} nombreRecurso={recurso} />
              )}
            </VistaConflicto>
          )}

          {estado.estadoRun === 'ESPERANDO_CAMPO' && estado.preguntasCampo.length > 0 && (
            <FormCampo preguntas={estado.preguntasCampo} enviando={run.enviando} error={run.errorAccion} onEnviar={run.confirmarCampo} />
          )}

          {bloqueado && (
            <EstadoBloqueado
              motivo={estado.plan?.motivo}
              causas={estado.conflictos.map((x) => x.causa)}
              alternativas={estado.alternativas}
              escalamiento={estado.plan?.escalamiento}
            />
          )}

          <div className="flex flex-wrap items-stretch gap-5">
            <BarraDecision
              estadoSistema={planActual?.estado_sistema ?? estado.estadoSistema}
              estadoRun={estado.estadoRun}
              requerida={estado.decisionRequerida}
              decision={estado.decision}
              planElegido={planActual?.id ?? null}
              resumenPlan={resumenPlan}
              enviando={run.enviando}
              error={estado.estadoRun === 'ESPERANDO_CAMPO' ? null : run.errorAccion}
              onDecidir={(d, comentario) => run.decidir(d, comentario, planActual?.id)}
              onExportar={() => exportarAuditoria(run)}
            />
            <LineaTiempo entradas={estado.lineaTiempo} />
          </div>
        </>
      )}
    </>
  )
}
