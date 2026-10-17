// Línea de tiempo de auditoría (RF-F2-34): eventos clave con actor y hora.
import type { EntradaLineaTiempo } from '@/eventos/reductor'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { nombreActor } from './insignias'

const hora = (ts: string) => new Date(ts).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

const DESTACADO: Partial<Record<EntradaLineaTiempo['tipo'], string>> = {
  'conflicto.detectado': 'border-red-400',
  'plan.listo': 'border-emerald-400',
  'humano.campo_confirmado': 'border-amber-400',
  'humano.decision_tomada': 'border-sky-400',
  'run.error': 'border-red-500',
}

export function LineaTiempo({ entradas }: { entradas: EntradaLineaTiempo[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Línea de tiempo (auditoría)</CardTitle>
      </CardHeader>
      <CardContent>
        {entradas.length === 0 ? (
          <p className="text-sm text-muted-foreground">Aún no hay eventos.</p>
        ) : (
          <ol className="grid gap-2">
            {entradas.map((e) => (
              <li key={e.seq} className={cn('grid grid-cols-[4.5rem_minmax(0,1fr)] gap-2 border-l-2 pl-3 text-sm', DESTACADO[e.tipo] ?? 'border-border')}>
                <time dateTime={e.ts} className="font-mono text-xs text-muted-foreground">{hora(e.ts)}</time>
                <div>
                  <div>{e.texto}</div>
                  <div className="text-xs text-muted-foreground">#{e.seq} · {nombreActor(e.actor)}</div>
                </div>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  )
}
