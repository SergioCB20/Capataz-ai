// Controles críticos (RF-F1-32): una fila por requisito con icono + texto, si es bloqueante y quién
// lo verificó. Con alternativas, un interruptor compara el plan original con el plan elegido.
import { ChevronRight } from 'lucide-react'
import { claveRequisito } from '@/eventos/reductor'
import type { FilaControl, FilaRequisito } from '@/eventos/vista'
import { cn } from '@/lib/utils'
import { EstadoControlBadge, InsigniaSimulado, nombreActor } from './insignias'

const TIPO_REQUISITO = { competencia: 'Competencia', equipo: 'Equipo', condicion_campo: 'Condición de campo' } as const

export type VistaPlan = 'original' | 'elegido'

export function TablaControles({ filas, seleccion, onElegir, comparar, vista, onVista, etiquetaElegido }: {
  filas: FilaControl[]
  seleccion: string | null
  onElegir: (control: FilaControl, requisito: FilaRequisito) => void
  /** Hay plan original y alternativa: se muestra el interruptor. */
  comparar: boolean
  vista: VistaPlan
  onVista: (v: VistaPlan) => void
  etiquetaElegido: string
}) {
  const requisitos = filas.flatMap((c) => c.requisitos.map((r) => ({ c, r })))
  const cumplen = requisitos.filter(({ r }) => r.resultado?.estado === 'CUMPLE').length
  const fallan = requisitos.filter(({ r }) => r.resultado?.estado === 'NO_CUMPLE').length
  const pendientes = requisitos.length - cumplen - fallan

  return (
    <section aria-labelledby="ctl" className="min-w-0 flex-[2_1_560px] rounded-[28px] bg-white px-6 py-6 sm:px-7">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 id="ctl" className="text-lg font-extrabold">Controles críticos</h2>
          <p className="mt-1 text-[13px] text-tenue">Elige un requisito para ver su evidencia.</p>
        </div>
        <dl className="m-0 flex items-center gap-6">
          {[['Cumplen', cumplen], ['No cumplen', fallan], ['Por verificar', pendientes]].map(([t, n]) => (
            <div key={t} className="text-center">
              <dd className="m-0 text-[30px] leading-none font-extrabold">{n}</dd>
              <dt className="mt-1 text-xs text-tenue">{t}</dt>
            </div>
          ))}
        </dl>
      </div>

      {comparar && (
        <div role="group" aria-label="Qué plan mostrar" className="mt-4 inline-grid grid-cols-2 gap-1 rounded-full bg-segmento p-1">
          {(['original', 'elegido'] as const).map((v) => (
            <button
              key={v}
              type="button"
              aria-pressed={vista === v}
              onClick={() => onVista(v)}
              className={cn(
                'min-h-10 rounded-full px-4 text-[13px] font-bold transition-colors focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-acento',
                vista === v ? 'bg-tinta text-white' : 'text-tinta-2 hover:bg-white',
              )}
            >
              {v === 'original' ? 'Plan original' : etiquetaElegido}
            </button>
          ))}
        </div>
      )}

      {requisitos.length === 0 ? (
        <p className="mt-6 text-sm text-tenue">El Agente Riesgo aún no ha identificado los controles que aplican.</p>
      ) : (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full min-w-[560px] border-collapse">
            <thead>
              <tr className="text-left text-xs text-tenue">
                <th scope="col" className="border-b border-linea px-2 py-3 font-semibold">Requisito</th>
                <th scope="col" className="border-b border-linea px-2 py-3 font-semibold">Tipo</th>
                <th scope="col" className="border-b border-linea px-2 py-3 font-semibold">Verificado por</th>
                <th scope="col" className="border-b border-linea px-2 py-3 font-semibold">Estado</th>
                <th scope="col" className="border-b border-linea px-2 py-3"><span className="sr-only">Ver evidencia</span></th>
              </tr>
            </thead>
            <tbody>
              {requisitos.map(({ c, r }) => {
                const clave = claveRequisito({ control_id: c.controlId, requisito_id: r.requisito.id })
                const sel = seleccion === clave
                return (
                  <tr key={clave} className={cn('transition-colors', sel ? 'bg-acento-fondo' : 'hover:bg-campo')}>
                    <td className="border-b border-[#F0EEF5] px-2 py-3.5">
                      <div className="text-sm font-bold">{r.requisito.descripcion}</div>
                      <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-tenue">
                        {c.nombre}
                        {c.bloqueante && <span className="rounded-md bg-segmento px-1.5 py-px font-bold text-tinta-2">Bloqueante</span>}
                        <InsigniaSimulado fuente={c.fuente} />
                      </div>
                    </td>
                    <td className="border-b border-[#F0EEF5] px-2 py-3.5 text-[13px]">{TIPO_REQUISITO[r.requisito.tipo]}</td>
                    <td className="border-b border-[#F0EEF5] px-2 py-3.5 text-[13px]">{r.resultado ? nombreActor(r.resultado.verificado_por) : '—'}</td>
                    <td className="border-b border-[#F0EEF5] px-2 py-3.5"><EstadoControlBadge estado={r.resultado?.estado ?? null} /></td>
                    <td className="border-b border-[#F0EEF5] px-2 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => onElegir(c, r)}
                        aria-label={`Ver evidencia de ${r.requisito.descripcion}`}
                        aria-pressed={sel}
                        className={cn(
                          'inline-grid size-11 place-items-center rounded-full transition-colors focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-acento',
                          sel ? 'bg-acento text-white' : 'border-[1.5px] border-[#DCD8E8] bg-white text-tinta hover:border-tinta',
                        )}
                      >
                        <ChevronRight aria-hidden className="size-[18px]" />
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
