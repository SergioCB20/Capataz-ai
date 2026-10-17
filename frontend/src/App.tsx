// PROVISIONAL (bloque 1): reproduce replays/e1.json y muestra el estado del reductor.
// En el bloque 2 se reemplaza por la pantalla de inicio y la vista de ejecución.
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { estadoInicial, reducir } from '@/eventos/reductor'
import { fuenteArchivo } from '@/eventos/fuentes'
import { replayLocal } from '@/replays'

export default function App() {
  const [estado, setEstado] = useState(estadoInicial)
  const [corrida, setCorrida] = useState(0)

  useEffect(() => {
    const eventos = replayLocal('E1')
    if (!eventos) return
    setEstado(estadoInicial())
    return fuenteArchivo(eventos, { velocidad: 2 })({ onEvento: (e) => setEstado((s) => reducir(s, e)) })
  }, [corrida])

  return (
    <main className="mx-auto max-w-4xl space-y-4 p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">CAPATAZ · replay E1 (prueba del reductor)</h1>
        <Button variant="outline" onClick={() => setCorrida((c) => c + 1)}>
          Reproducir de nuevo
        </Button>
      </header>
      <p className="text-sm text-muted-foreground">
        Estado del run: <b>{estado.estadoRun ?? '—'}</b> · Plan: <b>{estado.estadoSistema ?? '—'}</b> · Último evento: {estado.ultimoSeq}
      </p>
      <ul className="grid grid-cols-4 gap-2 text-sm">
        {Object.entries(estado.agentes).map(([id, a]) => (
          <li key={id} className="rounded-md border p-2">
            <b className="capitalize">{id}</b>
            <div>{a.estado}</div>
            <div className="text-muted-foreground">{a.herramientas.map((h) => h.nombre).join(', ')}</div>
          </li>
        ))}
      </ul>
      <pre className="max-h-[60vh] overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(estado, null, 2)}</pre>
    </main>
  )
}
