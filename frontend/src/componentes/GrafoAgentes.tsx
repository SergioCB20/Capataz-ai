// Grafo vivo de agentes (RF-F1-31): 4 nodos fijos con su estado y las herramientas invocadas.
import { Background, Handle, Position, ReactFlow, type Edge, type Node, type NodeProps } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { motion } from 'motion/react'
import { CircleAlert, CircleCheck, CircleDashed, Loader2, Wrench, type LucideIcon } from 'lucide-react'
import type { IdAgente } from '@/api/types'
import type { EstadoAgente, EstadoUI, VistaAgente } from '@/eventos/reductor'
import { cn } from '@/lib/utils'
import { NOMBRE_AGENTE } from './insignias'

const ESTADO: Record<EstadoAgente, { texto: string; icono: LucideIcon; clase: string }> = {
  inactivo: { texto: 'Inactivo', icono: CircleDashed, clase: 'border-linea bg-white text-tenue' },
  trabajando: { texto: 'Trabajando', icono: Loader2, clase: 'border-acento bg-acento-fondo text-tinta ring-4 ring-acento-suave' },
  completado: { texto: 'Completado', icono: CircleCheck, clase: 'border-[#3DBE76] bg-[#E9F8EF] text-tinta' },
  error: { texto: 'Error', icono: CircleAlert, clase: 'border-mal bg-mal-fondo text-mal' },
}

type DatosNodo = { id: IdAgente; agente: VistaAgente; rol: string }

function NodoAgente({ data }: NodeProps<Node<DatosNodo>>) {
  const { agente, id, rol } = data
  const e = ESTADO[agente.estado]
  const ultimas = agente.herramientas.slice(-3)
  return (
    <motion.div
      className={cn('w-56 rounded-2xl border-[1.5px] p-3.5 text-left transition-colors', e.clase)}
      animate={
        agente.estado === 'trabajando'
          ? { scale: [1, 1.035, 1], transition: { duration: 1.2, repeat: Infinity, ease: 'easeInOut' } }
          : agente.estado === 'completado'
            ? { scale: [1.06, 1], transition: { duration: 0.3 } }
            : { scale: 1 }
      }
    >
      <Handle type="target" position={Position.Top} className="opacity-0" />
      <div className="text-sm font-semibold">{NOMBRE_AGENTE[id]}</div>
      <div className="text-xs opacity-80">{rol}</div>
      <div className="mt-2 flex items-center gap-1 text-xs font-medium">
        <e.icono aria-hidden className={cn('size-3.5', agente.estado === 'trabajando' && 'animate-spin')} />
        {e.texto}
      </div>
      {ultimas.length > 0 && (
        <ul className="mt-2 space-y-0.5 text-[11px] opacity-90" aria-label="Herramientas invocadas">
          {ultimas.map((h, i) => (
            <li key={i} className="flex items-center gap-1 truncate" title={h.salida_resumen}>
              <Wrench aria-hidden className="size-3 shrink-0" />
              <span className="font-mono">{h.nombre}</span>
            </li>
          ))}
        </ul>
      )}
      <Handle type="source" position={Position.Bottom} className="opacity-0" />
    </motion.div>
  )
}

const tiposNodo = { agente: NodoAgente }

const POS: Record<IdAgente, { x: number; y: number; rol: string }> = {
  supervisor: { x: 250, y: 0, rol: 'Orquesta y consolida' },
  riesgo: { x: 0, y: 190, rol: 'Peligros, controles e incidentes' },
  personal: { x: 250, y: 190, rol: 'Competencias y turnos' },
  equipo: { x: 500, y: 190, rol: 'Estado y disponibilidad' },
}

export function GrafoAgentes({ agentes }: { agentes: EstadoUI['agentes'] }) {
  const nodos: Node<DatosNodo>[] = (Object.keys(POS) as IdAgente[]).map((id) => ({
    id,
    type: 'agente',
    position: { x: POS[id].x, y: POS[id].y },
    data: { id, agente: agentes[id], rol: POS[id].rol },
    draggable: false,
    selectable: false,
  }))
  const aristas: Edge[] = (['riesgo', 'personal', 'equipo'] as IdAgente[]).map((id) => ({
    id: `supervisor-${id}`,
    source: 'supervisor',
    target: id,
    animated: agentes[id].estado === 'trabajando',
  }))

  return (
    <div className="h-[300px] w-full rounded-[20px] bg-[#FAFAFD]" role="img" aria-label={`Agentes: ${(Object.keys(POS) as IdAgente[]).map((id) => `${NOMBRE_AGENTE[id]} ${ESTADO[agentes[id].estado].texto}`).join(', ')}`}>
      <ReactFlow
        nodes={nodos}
        edges={aristas}
        nodeTypes={tiposNodo}
        fitView
        fitViewOptions={{ padding: 0.1 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        preventScrolling={false}
      >
        <Background gap={16} size={1} color="#DCD8E8" />
      </ReactFlow>
    </div>
  )
}
