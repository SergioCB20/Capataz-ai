// Barra de decisión (RF-F1-34, RF-F2-33, RT-04): Aprobar / Rechazar (comentario obligatorio).
// Solo se aprueba un plan RECOMENDADO; si el backend pide `solo_rechazo` (plan BLOQUEADO, o requisitos
// que quedaron NO_VERIFICABLE sin preguntas de campo), solo se puede rechazar. El backend lo fuerza igual (409).
import { useState } from 'react'
import { Check, Loader2, X } from 'lucide-react'
import type { DecisionHumana, EstadoRun, EstadoSistema } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { EstadoSistemaBadge, nombreActor } from './insignias'

const FINAL: Partial<Record<EstadoRun, string>> = {
  APROBADA: 'Plan aprobado',
  RECHAZADA: 'Plan rechazado',
  BLOQUEADA: 'Plan bloqueado rechazado',
  ERROR: 'La evaluación terminó con error',
}

export function BarraDecision({ estadoSistema, estadoRun, requerida, decision, planElegido, enviando, error, onDecidir }: {
  estadoSistema: EstadoSistema | null
  estadoRun: EstadoRun | null
  requerida: { plan_id: string; solo_rechazo: boolean } | null
  decision: DecisionHumana | null
  /** Plan elegido cuando hay varias alternativas verificadas (se muestra para que quede claro qué se aprueba). */
  planElegido?: string | null
  enviando: boolean
  error: string | null
  onDecidir: (d: 'aprobar' | 'rechazar', comentario?: string) => void
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

  return (
    <div className="grid gap-3 rounded-xl border bg-card p-4" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="font-medium">Plan (PTW borrador)</span>
          <EstadoSistemaBadge estado={estadoSistema} />
          {planElegido && <span className="font-mono text-xs">{planElegido}</span>}
          <span className="text-xs text-muted-foreground">Borrador: CAPATAZ no firma ni autoriza; la persona responsable decide.</span>
        </div>

        {decision ? (
          <div className="text-sm">
            <b>{(estadoRun && FINAL[estadoRun]) ?? (decision.decision === 'aprobar' ? 'Aprobado' : 'Rechazado')}</b> <span className="font-mono text-xs">({decision.plan_id})</span> por {nombreActor(`humano:${decision.usuario}`)}
            {decision.comentario && <span className="text-muted-foreground"> — «{decision.comentario}»</span>}
          </div>
        ) : requerida ? (
          <div className="flex flex-wrap items-center gap-2">
            <Button
              onClick={() => onDecidir('aprobar')}
              disabled={enviando || soloRechazo}
              title={soloRechazo ? motivoSoloRechazo : undefined}
            >
              {enviando ? <Loader2 className="animate-spin" aria-hidden /> : <Check aria-hidden />}
              Aprobar
            </Button>
            <Button variant="destructive" onClick={() => setRechazando(true)} disabled={enviando}>
              <X aria-hidden /> Rechazar
            </Button>
          </div>
        ) : (
          <span className="text-sm text-muted-foreground">
            {estadoRun && FINAL[estadoRun] ? FINAL[estadoRun] : 'La decisión se habilita cuando el plan esté listo.'}
          </span>
        )}
      </div>

      {soloRechazo && requerida && !decision && (
        <p className="text-sm text-red-800 dark:text-red-200">{motivoSoloRechazo}</p>
      )}

      {rechazando && requerida && !decision && (
        <div className="grid gap-2">
          <label className="grid gap-1 text-sm">
            Motivo del rechazo (obligatorio)
            <Textarea
              value={comentario}
              aria-invalid={faltaComentario}
              onChange={(e) => {
                setComentario(e.target.value)
                setFaltaComentario(false)
              }}
              placeholder="Por qué no se aprueba este plan"
            />
          </label>
          {faltaComentario && <p className="text-xs text-red-700 dark:text-red-300">Escribe el motivo antes de rechazar.</p>}
          <div className="flex gap-2">
            <Button variant="destructive" onClick={enviarRechazo} disabled={enviando}>Confirmar rechazo</Button>
            <Button variant="ghost" onClick={() => setRechazando(false)}>Cancelar</Button>
          </div>
        </div>
      )}

      {error && <p role="alert" className="text-sm text-red-700 dark:text-red-300">{error}</p>}
    </div>
  )
}
