// Cruza el estado del reductor con el catálogo para pintar el semáforo y el cajón.
// No calcula estados de control: solo muestra los que llegan en los eventos (RT-02; la lógica
// de «gana el peor» vive en el backend, en consolidar_control).
import type { Catalogo, Control, EstadoControl, Fuente, Incidente, Requisito, ResultadoRequisito } from '@/api/types'
import { claveRequisito, type EstadoUI } from './reductor'

export interface FilaRequisito {
  requisito: Requisito
  resultado: ResultadoRequisito | null
}

export interface FilaControl {
  controlId: string
  nombre: string
  bloqueante: boolean
  fuente: Fuente | null
  peligroId: string | null
  /** null = aún sin consolidar (se muestra «En verificación», nunca CUMPLE). */
  estado: EstadoControl | null
  requisitos: FilaRequisito[]
}

export function filasControles(estado: EstadoUI, catalogo: Catalogo): FilaControl[] {
  const ids: string[] = []
  const agregar = (id: string) => !ids.includes(id) && ids.push(id)
  estado.evaluacion?.peligros.forEach((p) => p.controles.forEach(agregar))
  estado.resultadosControl.forEach((c) => agregar(c.control_id))
  Object.values(estado.resultadosRequisito).forEach((r) => agregar(r.control_id))

  return ids.map((id) => {
    const control: Control | undefined = catalogo.controles.find((c) => c.id === id)
    const consolidado = estado.resultadosControl.find((c) => c.control_id === id)
    const peligro = estado.evaluacion?.peligros.find((p) => p.controles.includes(id))

    const requisitos: Requisito[] = control?.requisitos ?? []
    // Requisitos con resultado que no están en el catálogo local (p. ej. catálogo de demo desactualizado).
    const extra = Object.values(estado.resultadosRequisito).filter(
      (r) => r.control_id === id && !requisitos.some((q) => q.id === r.requisito_id),
    )
    const filas: FilaRequisito[] = [
      ...requisitos.map((requisito) => ({
        requisito,
        resultado: estado.resultadosRequisito[claveRequisito({ control_id: id, requisito_id: requisito.id })] ?? null,
      })),
      ...extra.map((r) => ({
        requisito: {
          id: r.requisito_id, tipo: 'competencia' as const, descripcion: r.requisito_id,
          certificacion: null, certificaciones_equivalentes: [], tipo_equipo: null, pregunta_campo: null,
        },
        resultado: r,
      })),
    ]

    return {
      controlId: id,
      nombre: control?.nombre ?? id,
      bloqueante: consolidado?.bloqueante ?? control?.bloqueante ?? true,
      fuente: control?.fuente ?? null,
      peligroId: control?.peligro_id ?? peligro?.peligro_id ?? null,
      estado: consolidado?.estado ?? null,
      requisitos: filas,
    }
  })
}

/** Incidentes similares de los peligros que piden este control (IDs reales del catálogo). */
export function incidentesDeControl(estado: EstadoUI, catalogo: Catalogo, controlId: string): (Incidente | { id: string })[] {
  const ids = new Set<string>()
  estado.evaluacion?.peligros.filter((p) => p.controles.includes(controlId)).forEach((p) => p.incidentes_similares.forEach((i) => ids.add(i)))
  return [...ids].map((id) => catalogo.incidentes.find((i) => i.id === id) ?? { id })
}

/** Nombre legible de una persona o equipo por ID; turnos `AAAA-MM-DD/dia|noche` => «día 17/10». Si no se reconoce, el texto tal cual. */
export function nombreRecurso(catalogo: Catalogo, valor: string): string {
  const persona = catalogo.personas.find((p) => p.id === valor)
  if (persona) return `${persona.nombre} (${valor})`
  const equipo = catalogo.equipos.find((e) => e.id === valor)
  if (equipo) return `${equipo.nombre} (${valor})`
  const turno = /^(\d{4})-(\d{2})-(\d{2})\/(dia|noche)$/.exec(valor)
  if (turno) return `${turno[4] === 'dia' ? 'día' : 'noche'} ${turno[3]}/${turno[2]}`
  return valor
}

export const nombrePeligro = (catalogo: Catalogo, id: string | null) =>
  (id && (catalogo.peligros.find((p) => p.id === id)?.nombre as string | undefined)) || id || ''
