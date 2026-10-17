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
