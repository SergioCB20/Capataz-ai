## Context

Las herramientas son funciones puras sobre el `Catalogo`, sin LLM ni red. P3 programa contra los acuerdos de interfaz de `p1-contrato-api-runtime/design.md` y prueba con *fixtures* propias, sin esperar los datos de P4.

## Goals / Non-Goals

**Goals:**
- Funciones puras y probadas para Personal, Equipo e Incidentes.
- Agentes que siempre devuelven evidencia; sin evidencia no hay `CUMPLE`.

**Non-Goals:**
- Orquestación y LLM (P2); datos semilla reales (P4).

## Decisions

- **Funciones puras + agente delgado.** `tools/personal.py`, `tools/equipo.py` y `tools/incidentes.py` no conocen eventos; `agents/personal.py` y `agents/equipo.py` las llaman, arman `ResultadoRequisito` y emiten `agente.herramienta` con un `TraceHerramienta` medido con `time.perf_counter`.
- **Fecha de referencia = fecha del turno.** La vigencia de una certificación se evalúa contra `tarea.turno.fecha`, no contra la fecha del sistema, para que los escenarios sean reproducibles.
- **Equivalencias por bandera.** `permitir_equivalencias` llega en `AgenteSolicitud`; en la primera pasada se ignoran `tipos_equivalentes` (RT-06).
- **Orden de `buscar_incidentes`.** Filtra por coincidencia de `equipo`, `actividad` o `riesgo_critico`, puntúa por cantidad de coincidencias y desempata por `nivel_potencial` descendente.
- **Evaluación con herramientas reales y LLM fake.** `evaluar` llama a `ejecutar_run` de P2 en modo fake; si P2 no está listo, evalúa solo las herramientas.

## Risks / Trade-offs

- [El formato de `nivel_potencial` del dataset no se conoce] → Tratarlo como texto ordinal con una tabla de orden configurable hasta que P4 confirme las columnas.
- [Fixtures distintas de los seeds de P4] → Al integrar, correr las pruebas también contra `data/*.json`.

## Reglas de datos que P3 asume (para P4 y P2)

> El contrato no dice cómo interpretar algunos campos. Esto es lo que implementan las herramientas; si P4 modela los datos de otra forma, avisen a P3 antes de cambiarlo.

### Personal (`tools/personal.py`, `agents/personal.py`)

- **Disponible en un turno** = ese `TurnoRef` está en `Persona.turnos`. Una lista vacía significa «nunca disponible», no «sin restricciones»: cada persona debe listar los turnos en que puede trabajar.
- **Vigencia**: una certificación vale si `vence` ≥ fecha del turno (el día de vencimiento todavía vale). Se usa la fecha del turno, no la del sistema.
- **Equivalencias**: `Requisito.certificaciones_equivalentes` solo cuentan cuando `AgenteSolicitud.permitir_equivalencias` es verdadero (alternativas), nunca en la primera pasada.
- **Doble asignación** = otra tarea del catálogo (`Catalogo.escenarios[].tarea`, con distinto `id`) en el **mismo turno** que ya asigna a la misma persona. El contrato no tiene un campo «ocupado en», así que esa es la única fuente.
  - **Cuidado al diseñar los escenarios:** si dos escenarios (p. ej. E1 y E2c) asignan a la misma persona en el mismo turno, cada uno verá al otro como doble asignación y fallará. Usen turnos o personas distintos entre escenarios, salvo para inyectar a propósito una doble asignación (un caso de evaluación puede reutilizar persona y turno de un escenario).
- Basta **una** persona asignada que cumpla (certificación vigente + disponible + sin doble asignación) para que el requisito sea `CUMPLE`. Una persona asignada que no existe en el catálogo no cuenta y, si no se pudo evaluar a nadie, el requisito queda `NO_VERIFICABLE` (no `NO_CUMPLE`).

### Equipo (`tools/equipo.py`, `agents/equipo.py`)

- **Cubre el tipo** si `Equipo.tipo_equipo` coincide con `Requisito.tipo_equipo`. Con `permitir_equivalencias`, también si el tipo requerido está en `Equipo.tipos_equivalentes` (es decir, `tipos_equivalentes` lista **otros tipos que este equipo puede cubrir**; p. ej. una perforadora con `["empernador"]` puede hacer de empernador en una alternativa).
- **Utilizable** si `estado` es `operativo` **y** el turno no figura en `Equipo.mantenimiento`. `estado = mantenimiento | fuera_servicio` lo descarta siempre; `mantenimiento` (lista de turnos) es una indisponibilidad programada solo para esos turnos. Por eso `reprogramar_turno` solo arregla un equipo con mantenimiento **programado**, no uno con `estado = mantenimiento`.
- Basta **un** equipo asignado que cubra el tipo y sea utilizable. No se verifica doble asignación de equipos (el requisito RF-F1-14 no la pide).

### `buscar_incidentes` (`tools/incidentes.py`)

- Compara palabras (sin tildes ni mayúsculas, raíz simple) de `equipo`, `actividad` y `riesgo_critico` con los campos del incidente: `equipo`; `actividad` y `tipo_tarea`; `riesgo_critico` (2 puntos) y `descripcion` (1 punto). Ordena por puntos, luego `nivel_potencial` (mayor primero), fecha reciente e id. Máximo 5.
- **`nivel_potencial`**: se entienden niveles romanos `I`–`VI` (como el dataset de Kaggle), `bajo|medio|alto|critico|catastrofico` y dígitos; cualquier otro valor pesa 0. Confirmen con P4 el formato real (`ORDEN_NIVEL` es configurable).
- Para que el Agente Riesgo encuentre incidentes útiles, `Incidente.actividad`, `equipo`, `riesgo_critico` y `descripcion` deben estar en español natural y coincidir en vocabulario con los nombres de `TipoTarea`, `Peligro` y `Equipo`.

### Checklist dinámico y evaluación (impacto en los datos)

- El Agente Riesgo suma el `control_fallido` de los **2 incidentes más relevantes** de cada peligro (también el modo fake). Por eso un escenario «limpio» (E1) solo sale `RECOMENDADO` si **también** cumple esos controles adicionales: revisen que los incidentes parecidos a E1 no apunten a controles que E1 incumple.
- Un caso de evaluación «detectable por incidentes» necesita que el tipo de tarea tenga **al menos un control base** (el Riesgo deduce los peligros de los controles que aplican) y que el control adicional llegue por `control_fallido` de un incidente similar.
- `scripts/evaluar.py`: `uv run --project backend python scripts/evaluar.py` (lee `data/` y `data/evaluacion.json`; `--data-dir`, `--casos`, `--json`, `--sin-json`). Una falla está **detectada** si el estado de la primera pasada coincide con `resultado_esperado`; se atribuye a «checklist base» si ya lo detecta sin `buscar_incidentes` y a «incidentes» si solo lo detecta con él. Compara además con `detectable_por` del caso. Un caso limpio es falso positivo si no sale como se esperaba. El reporte tiene el encabezado «DATOS SIMULADOS» y es reproducible (sin fechas ni tiempos).
