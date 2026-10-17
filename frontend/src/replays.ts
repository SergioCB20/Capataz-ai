// Replays empaquetados en el build: permiten reproducir sin backend (demo sin red y vitrina
// de Vercel, RF-F3-45/46). Lee ../replays/<escenario_id>.json (los graba P1; e1.json es provisional).
import type { Evento } from '@/api/types'

const archivos = import.meta.glob<Evento[]>('../../replays/*.json', { eager: true, import: 'default' })

export const replaysLocales: Record<string, Evento[]> = Object.fromEntries(
  Object.entries(archivos).map(([ruta, eventos]) => [ruta.split('/').pop()!.replace(/\.json$/, '').toUpperCase(), eventos]),
)

/** Eventos del replay local de un escenario (`E1`, `E2`, `E2C`, `E3`), o null si no existe. */
export const replayLocal = (escenarioId: string): Evento[] | null => replaysLocales[escenarioId.toUpperCase()] ?? null
