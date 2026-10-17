// Catálogo de DEMOSTRACIÓN para trabajar sin backend. Datos 100 % simulados (RT-07).
// Cuando el backend responde, la UI usa GET /api/catalogo (seeds de P4) y este archivo no se usa.
// Los IDs coinciden con replays/e1.json.
import type { Catalogo, Certificacion, Fuente, Requisito, Tarea } from '@/api/types'

const SIM: Fuente = { tipo: 'simulado', referencia: 'Catálogo de demostración del frontend', url: null }

const req = (r: Pick<Requisito, 'id' | 'tipo' | 'descripcion'> & Partial<Requisito>): Requisito => ({
  certificacion: null, certificaciones_equivalentes: [], tipo_equipo: null, pregunta_campo: null, ...r,
})
const cert = (codigo: string, vence: string): Certificacion => ({ codigo, vence, nombre: null })

const tarea = (id: string, tipo_tarea: string, descripcion: string, zona: string, turno: 'dia' | 'noche',
  personas: string[], equipos: string[]): Tarea => ({
  id, tipo_tarea, descripcion, zona, turno: { fecha: '2026-10-17', turno }, asignacion: { personas, equipos },
})

export const catalogoDemo: Catalogo = {
  peligros: [
    { id: 'pel-caida-rocas', nombre: 'Caída de rocas', descripcion: '', fuente: SIM },
    { id: 'pel-energia', nombre: 'Energía peligrosa (hidráulica / eléctrica)', descripcion: '', fuente: SIM },
    { id: 'pel-gases', nombre: 'Atmósfera peligrosa (gases, falta de oxígeno)', descripcion: '', fuente: SIM },
  ],
  tipos_tarea: [
    { id: 'sostenimiento_pernos', nombre: 'Sostenimiento con pernos', descripcion: '' },
    { id: 'desatado_rocas', nombre: 'Desatado de rocas', descripcion: '' },
    { id: 'limpieza_labor', nombre: 'Limpieza de labor con scoop', descripcion: '' },
  ],
  controles: [
    {
      id: 'ctl-sostenimiento', nombre: 'Sostenimiento ejecutado por operador certificado con equipo apto',
      peligro_id: 'pel-caida-rocas', bloqueante: true, aplica_a: ['sostenimiento_pernos', 'desatado_rocas'], fuente: SIM,
      requisitos: [
        req({ id: 'req-operador-empernador', tipo: 'competencia', descripcion: 'Operador con certificación OP-EMPERNADOR vigente', certificacion: 'OP-EMPERNADOR' }),
        req({ id: 'req-jumbo-operativo', tipo: 'equipo', descripcion: 'Jumbo empernador operativo y disponible en el turno', tipo_equipo: 'jumbo_empernador' }),
      ],
    },
    {
      id: 'ctl-loto', nombre: 'Bloqueo y etiquetado de energías (LOTO)',
      peligro_id: 'pel-energia', bloqueante: true, aplica_a: ['sostenimiento_pernos', 'limpieza_labor'], fuente: SIM,
      requisitos: [req({ id: 'req-loto', tipo: 'competencia', descripcion: 'Personal con capacitación LOTO vigente', certificacion: 'LOTO' })],
    },
    {
      id: 'ctl-epp', nombre: 'Inducción de seguridad y EPP',
      peligro_id: 'pel-caida-rocas', bloqueante: false, aplica_a: ['sostenimiento_pernos', 'desatado_rocas', 'limpieza_labor'], fuente: SIM,
      requisitos: [req({ id: 'req-induccion', tipo: 'competencia', descripcion: 'Inducción de seguridad vigente', certificacion: 'INDUCCION-SSO' })],
    },
    {
      id: 'ctl-ventilacion', nombre: 'Ventilación y medición de gases antes del ingreso',
      peligro_id: 'pel-gases', bloqueante: true, aplica_a: ['sostenimiento_pernos', 'desatado_rocas', 'limpieza_labor'], fuente: SIM,
      requisitos: [req({ id: 'req-ventilacion', tipo: 'condicion_campo', descripcion: 'Medición de gases conforme en la labor', pregunta_campo: '¿La medición de gases en la labor está dentro de límites y la ventilación funciona?' })],
    },
  ],
  personas: [
    { id: 'p-001', nombre: 'Operador A (Luis)', rol: 'Operador de jumbo', fuente: SIM, turnos: [{ fecha: '2026-10-17', turno: 'dia' }],
      certificaciones: [cert('OP-EMPERNADOR', '2027-03-31'), cert('LOTO', '2026-12-15'), cert('INDUCCION-SSO', '2027-01-10')] },
    { id: 'p-002', nombre: 'Ayudante B (Rosa)', rol: 'Ayudante', fuente: SIM, turnos: [{ fecha: '2026-10-17', turno: 'dia' }],
      certificaciones: [cert('INDUCCION-SSO', '2026-11-30')] },
    { id: 'p-003', nombre: 'Operador C (Jorge)', rol: 'Operador de jumbo', fuente: SIM, turnos: [{ fecha: '2026-10-17', turno: 'noche' }],
      certificaciones: [cert('OP-EMPERNADOR', '2026-09-30'), cert('LOTO', '2027-02-01'), cert('INDUCCION-SSO', '2027-01-10')] },
    { id: 'p-004', nombre: 'Operador D (Ana)', rol: 'Operador de jumbo', fuente: SIM, turnos: [{ fecha: '2026-10-17', turno: 'noche' }],
      certificaciones: [cert('OP-EMPERNADOR', '2027-05-20'), cert('LOTO', '2027-05-20'), cert('INDUCCION-SSO', '2027-05-20')] },
  ],
  equipos: [
    { id: 'eq-jumbo-01', nombre: 'Jumbo empernador 01', tipo_equipo: 'jumbo_empernador', estado: 'operativo', tipos_equivalentes: [], mantenimiento: [], fuente: SIM },
    { id: 'eq-jumbo-02', nombre: 'Jumbo empernador 02', tipo_equipo: 'jumbo_empernador', estado: 'mantenimiento', tipos_equivalentes: [], mantenimiento: [], fuente: SIM },
    { id: 'eq-bolter-01', nombre: 'Bolter 01', tipo_equipo: 'bolter', estado: 'operativo', tipos_equivalentes: ['jumbo_empernador'], mantenimiento: [], fuente: SIM },
  ],
  incidentes: [
    { id: 'inc-007', fecha: '2025-03-14', planta: 'Mina subterránea A', nivel_real: 'II', nivel_potencial: 'V', riesgo_critico: 'caida_rocas',
      descripcion: 'Desprendimiento de roca en labor recién disparada antes de completar el sostenimiento; el operador estaba bajo techo sin sostener.',
      equipo: 'jumbo_empernador', actividad: 'sostenimiento', tipo_tarea: 'sostenimiento_pernos', causa_raiz: 'Desatado incompleto',
      control_fallido: 'ctl-sostenimiento', fuente: SIM },
    { id: 'inc-021', fecha: '2024-11-02', planta: 'Mina subterránea B', nivel_real: 'I', nivel_potencial: 'IV', riesgo_critico: 'caida_rocas',
      descripcion: 'Caída de bloque pequeño durante el empernado; el operador no tenía la certificación vigente para el equipo.',
      equipo: 'jumbo_empernador', actividad: 'sostenimiento', tipo_tarea: 'sostenimiento_pernos', causa_raiz: 'Competencia no verificada',
      control_fallido: 'ctl-sostenimiento', fuente: SIM },
    { id: 'inc-033', fecha: '2025-06-21', planta: 'Mina subterránea A', nivel_real: 'II', nivel_potencial: 'IV', riesgo_critico: 'atmosfera_peligrosa',
      descripcion: 'Ingreso a labor sin medición de gases tras voladura; dos trabajadores con síntomas leves.',
      equipo: 'ventilador_auxiliar', actividad: 'ingreso_labor', tipo_tarea: 'desatado_rocas', causa_raiz: 'Medición omitida',
      control_fallido: 'ctl-ventilacion', fuente: SIM },
  ],
  escenarios: [
    { id: 'E1', nombre: 'Caso limpio', resultado_esperado: 'RECOMENDADO', escalamiento: null,
      tarea: tarea('t-e1', 'sostenimiento_pernos', 'Sostenimiento con pernos helicoidales en labor 12 tras voladura', 'Nivel 3200 · Labor 12', 'dia', ['p-001', 'p-002'], ['eq-jumbo-01']) },
    { id: 'E2', nombre: 'Conflicto con alternativas', resultado_esperado: 'RECOMENDADO', escalamiento: null,
      tarea: tarea('t-e2', 'sostenimiento_pernos', 'Sostenimiento en labor 15 con jumbo en mantenimiento', 'Nivel 3150 · Labor 15', 'noche', ['p-003'], ['eq-jumbo-02']) },
    { id: 'E2c', nombre: 'Requisito de campo', resultado_esperado: 'REQUIERE_CAMPO', escalamiento: null,
      tarea: tarea('t-e2c', 'desatado_rocas', 'Desatado de rocas tras voladura en labor 8', 'Nivel 3200 · Labor 8', 'dia', ['p-001'], ['eq-jumbo-01']) },
    { id: 'E3', nombre: 'Bloqueo sin alternativa segura', resultado_esperado: 'BLOQUEADO', escalamiento: 'Jefe de guardia',
      tarea: tarea('t-e3', 'sostenimiento_pernos', 'Sostenimiento urgente en labor 20 sin equipo ni operador disponibles', 'Nivel 3100 · Labor 20', 'noche', ['p-003'], ['eq-jumbo-02']) },
  ],
}
