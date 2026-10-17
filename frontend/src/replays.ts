// Replays empaquetados en el build: permiten reproducir sin backend (demo sin red y vitrina
// de Vercel, RF-F3-45/46). Prioridad: ../replays/<escenario_id>.json (grabados por P1 desde
// corridas reales) y, si falta alguno, los fixtures escritos a mano en src/__fixtures__ (provisionales).
import type { Evento } from '@/api/types'

const grabados = import.meta.glob<Evento[]>('../../replays/*.json', { eager: true, import: 'default' })
const fixtures = import.meta.glob<Evento[]>('./__fixtures__/*.json', { eager: true, import: 'default' })

const porEscenario = (archivos: Record<string, Evento[]>) =>
  Object.fromEntries(
    Object.entries(archivos).map(([ruta, eventos]) => [ruta.split('/').pop()!.replace(/\.json$/, '').toUpperCase(), eventos]),
  )

export const replaysLocales: Record<string, Evento[]> = { ...porEscenario(fixtures), ...porEscenario(grabados) }

/** Eventos del replay local de un escenario (`E1`, `E2`, `E2c`, `E3`), o null si no existe. */
export const replayLocal = (escenarioId: string): Evento[] | null => replaysLocales[escenarioId.toUpperCase()] ?? null
