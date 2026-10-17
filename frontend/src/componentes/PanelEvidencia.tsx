// Evidencia del requisito elegido (RF-F1-33): estado, agente que verificó, registros consultados
// y los incidentes similares, todo marcado «simulado» cuando corresponde.
import type { Incidente } from '@/api/types'
import type { FilaControl, FilaRequisito } from '@/eventos/vista'
import { EstadoControlBadge, InsigniaSimulado, nombreActor } from './insignias'

const TIPO_FUENTE = { normativa: 'Normativa', guia: 'Guía', simulado: 'Dato simulado' } as const

export function PanelEvidencia({ seleccion, incidentes }: {
  seleccion: { control: FilaControl; requisito: FilaRequisito } | null
  incidentes: (Incidente | { id: string })[]
}) {
  const r = seleccion?.requisito.resultado ?? null
  return (
    <aside aria-labelledby="evi" aria-live="polite" className="flex min-w-0 flex-[1_1_320px] flex-col gap-3.5 rounded-[28px] bg-white px-6 py-6 sm:px-7">
      <div className="flex items-center justify-between gap-2">
        <h2 id="evi" className="text-lg font-extrabold">Evidencia</h2>
        {seleccion && <EstadoControlBadge estado={r?.estado ?? null} />}
      </div>

      {!seleccion ? (
        <p className="text-sm text-tenue">Elige un requisito de la tabla para ver qué se consultó y quién lo verificó.</p>
      ) : (
        <>
          <div>
            <div className="text-[15px] font-extrabold">{seleccion.requisito.requisito.descripcion}</div>
            <div className="mt-0.5 text-[13px] text-tenue">
              {r ? (
                <>Verificado por <b className="text-tinta">{nombreActor(r.verificado_por)}</b> con herramienta determinista</>
              ) : (
                'Aún en verificación'
              )}
            </div>
          </div>
          {r?.detalle && <p className="m-0 text-sm leading-relaxed">{r.detalle}</p>}

          {r && r.evidencia.length === 0 && (
            <p className="m-0 rounded-2xl bg-aviso-fondo p-3 text-[13px] text-aviso">Sin evidencia registrada: por eso no puede ser CUMPLE.</p>
          )}
          {r?.evidencia.map((ev, i) => (
            <div key={i} className="flex flex-col gap-1.5 rounded-2xl bg-campo p-3.5">
              <span className="font-mono text-xs text-tenue">{ev.registro}</span>
              <span className="text-sm">
                {ev.campo}: <b>{String(ev.valor)}</b>
              </span>
              <span className="flex flex-wrap items-center gap-1.5 text-xs text-tenue">
                {TIPO_FUENTE[ev.fuente.tipo]} ·{' '}
                {ev.fuente.url ? <a className="underline" href={ev.fuente.url} target="_blank" rel="noreferrer">{ev.fuente.referencia}</a> : ev.fuente.referencia}
                <InsigniaSimulado fuente={ev.fuente} />
              </span>
            </div>
          ))}

          <h3 className="mt-1.5 text-sm font-extrabold">Incidentes similares</h3>
          {incidentes.length === 0 ? (
            <p className="m-0 text-[13px] text-tenue">El Agente Riesgo no asoció incidentes a este control.</p>
          ) : (
            incidentes.map((inc) => (
              <div key={inc.id} className="flex flex-col gap-1.5 rounded-2xl border border-linea px-3.5 py-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs">{inc.id}</span>
                  <InsigniaSimulado fuente={'fuente' in inc ? inc.fuente : null} />
                </div>
                {'descripcion' in inc ? (
                  <>
                    <span className="text-[13px] leading-snug">{inc.descripcion}</span>
                    <span className="text-xs text-tenue">
                      {inc.fecha} · potencial {inc.nivel_potencial} · causa: {inc.causa_raiz}
                    </span>
                  </>
                ) : (
                  <span className="text-[13px] text-tenue">Detalle no disponible en el catálogo cargado.</span>
                )}
              </div>
            ))
          )}
        </>
      )}
    </aside>
  )
}
