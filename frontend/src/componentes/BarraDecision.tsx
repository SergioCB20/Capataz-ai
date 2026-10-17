// Tu decisión (RF-F1-34, RF-F2-33, RT-04): Aprobar / Rechazar (comentario obligatorio).
// Solo se aprueba un plan RECOMENDADO; si el backend pide `solo_rechazo` (plan BLOQUEADO, o requisitos
// que quedaron NO_VERIFICABLE sin preguntas de campo), solo se puede rechazar. El backend lo fuerza igual (409).
import { useState } from 'react'
import { Check, Loader2, X } from 'lucide-react'
import type { DecisionHumana, EstadoRun, EstadoSistema } from '@/api/types'
import { nombreActor } from './insignias'

const FINAL: Partial<Record<EstadoRun, string>> = {
  APROBADA: 'Plan aprobado',
  RECHAZADA: 'Plan rechazado',
  BLOQUEADA: 'Plan bloqueado rechazado',
  ERROR: 'La evaluación terminó con error',
}

const btn = 'min-h-[52px] rounded-full px-6 text-[15px] font-extrabold transition-opacity focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-white disabled:cursor-not-allowed disabled:opacity-50'

export function BarraDecision({ estadoSistema, estadoRun, requerida, decision, planElegido, resumenPlan, enviando, error, onDecidir, onExportar }: {
  estadoSistema: EstadoSistema | null
  estadoRun: EstadoRun | null
  requerida: { plan_id: string; solo_rechazo: boolean } | null
  decision: DecisionHumana | null
  /** Plan sobre el que se decide (el elegido entre las alternativas verificadas). */
  planElegido: string | null
  /** Una línea que describe el plan elegido. */
  resumenPlan: string | null
  enviando: boolean
  error: string | null
  onDecidir: (d: 'aprobar' | 'rechazar', comentario?: string) => void
  onExportar?: () => void
}) {
  const [rechazando, setRechazando] = useState(false)
  const [comentario, setComentario] = useState('')
  const [faltaComentario, setFaltaComentario] = useState(false)
  const soloRechazo = requerida?.solo_rechazo || estadoSistema === 'BLOQUEADO'
  const motivoSoloRechazo =
    estadoSistema === 'BLOQUEADO'
      ? 'El plan está BLOQUEADO: solo se puede rechazar, con un comentario.'
      : 'Este plan no se puede aprobar: quedan requisitos sin verificar (NO_VERIFICABLE). Solo se puede rechazar, con un comentario.'

  const enviarRechazo = () => {
    if (!comentario.trim()) return setFaltaComentario(true)
    onDecidir('rechazar', comentario.trim())
  }
  const aprobado = decision?.decision === 'aprobar'

  return (
    <section aria-labelledby="dec" aria-live="polite" className="flex min-w-0 flex-[2_1_520px] flex-col gap-4 rounded-[28px] bg-tinta px-7 py-6 text-white">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="dec" className="text-xl font-extrabold">Tu decisión</h2>
        <span className="text-xs text-[#BDB8CC]">Plan (PTW borrador): CAPATAZ no firma ni autoriza.</span>
      </div>

      {decision ? (
        <>
          <div className="flex items-start gap-3.5">
            <span aria-hidden className={'grid size-11 flex-none place-items-center rounded-full ' + (aprobado ? 'bg-[#A7EBC2] text-[#0B3D20]' : 'bg-[#FFB4AB] text-[#3B0A06]')}>
              {aprobado ? <Check className="size-[22px]" strokeWidth={3} /> : <X className="size-[22px]" strokeWidth={3} />}
            </span>
            <div>
              <div className="text-lg font-extrabold">
                {(estadoRun && FINAL[estadoRun]) ?? (aprobado ? 'Plan aprobado' : 'Plan rechazado')} <span className="font-mono text-sm font-medium">({decision.plan_id})</span>
              </div>
              <p className="mt-1.5 text-sm leading-relaxed text-[#D9D5E6]">
                Por {nombreActor(`humano:${decision.usuario}`)}.{' '}
                {decision.comentario ? `Motivo: «${decision.comentario}». ` : ''}
                Quedó registrado en la auditoría con usuario y hora.
              </p>
            </div>
          </div>
          {onExportar && (
            <div>
              <button type="button" onClick={onExportar} className={btn + ' bg-white text-tinta'}>Exportar auditoría (JSON)</button>
            </div>
          )}
        </>
      ) : requerida ? (
        <>
          <p className="m-0 text-[15px] leading-relaxed text-[#D9D5E6]">
            Vas a decidir sobre el plan <b className="font-mono text-white">{planElegido ?? requerida.plan_id}</b>
            {resumenPlan ? `: ${resumenPlan}` : '.'}
          </p>
          {soloRechazo && <p className="m-0 rounded-2xl bg-[#3A1B1F] px-4 py-3 text-sm font-semibold text-[#FFB4AB]">{motivoSoloRechazo}</p>}
          {!rechazando ? (
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => onDecidir('aprobar')}
                disabled={enviando || soloRechazo}
                title={soloRechazo ? motivoSoloRechazo : undefined}
                className={btn + ' inline-flex items-center gap-2 bg-[#8F75FF] text-tinta'}
              >
                {enviando && <Loader2 aria-hidden className="size-4 animate-spin" />}
                Aprobar plan
              </button>
              <button type="button" onClick={() => setRechazando(true)} disabled={enviando} className={btn + ' border-[1.5px] border-[#6E6A7C] bg-transparent text-white'}>
                Rechazar
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              <label className="flex flex-col gap-2 text-sm font-bold">
                Motivo del rechazo (obligatorio)
                <textarea
                  rows={3}
                  value={comentario}
                  aria-invalid={faltaComentario}
                  onChange={(e) => {
                    setComentario(e.target.value)
                    setFaltaComentario(false)
                  }}
                  placeholder="Por qué no se aprueba este plan"
                  className="resize-y rounded-[14px] border-[1.5px] border-[#4A4659] bg-[#24212F] px-3.5 py-3 text-[15px] font-medium text-white placeholder:text-[#9A95AB] focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-white"
                />
              </label>
              {faltaComentario && <p className="m-0 text-[13px] font-bold text-[#FFB4AB]">Escribe el motivo antes de confirmar el rechazo.</p>}
              <div className="flex flex-wrap gap-3">
                <button type="button" onClick={enviarRechazo} disabled={enviando} className={btn + ' bg-[#FFB4AB] text-[#3B0A06]'}>Confirmar rechazo</button>
                <button type="button" onClick={() => setRechazando(false)} className={btn + ' bg-transparent text-[#D9D5E6]'}>Cancelar</button>
              </div>
            </div>
          )}
        </>
      ) : (
        <p className="m-0 text-[15px] text-[#D9D5E6]">
          {estadoRun && FINAL[estadoRun]
            ? FINAL[estadoRun]
            : estadoRun === 'ESPERANDO_CAMPO'
              ? 'Primero confirma los requisitos de campo; después podrás decidir.'
              : 'La decisión se habilita cuando el plan esté listo.'}
        </p>
      )}

      {error && <p role="alert" className="m-0 text-sm font-semibold text-[#FFB4AB]">{error}</p>}
    </section>
  )
}
