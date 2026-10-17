// Replays empaquetados en el build: permiten reproducir sin backend (demo sin red y vitrina
// de Vercel, RF-F3-45/46). Son los grabados desde corridas reales en ../replays/<escenario_id>.json
// (scripts/grabar_replay.py). Los fixtures de src/__fixtures__ son solo para los tests.
import type { Evento } from '@/api/types'

const grabados = import.meta.glob<Evento[]>('../../replays/*.json', { eager: true, import: 'default' })

export const replaysLocales: Record<string, Evento[]> = Object.fromEntries(
  Object.entries(grabados).map(([ruta, eventos]) => [ruta.split('/').pop()!.replace(/\.json$/, '').toUpperCase(), eventos]),
)

/** Eventos del replay local de un escenario (`E1`, `E2`, `E2c`, `E3`), o null si no existe. */
export const replayLocal = (escenarioId: string): Evento[] | null => replaysLocales[escenarioId.toUpperCase()] ?? null
