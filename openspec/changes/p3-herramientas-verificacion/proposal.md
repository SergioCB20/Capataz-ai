## Why

El principio central de CAPATAZ es que el código verifica y el LLM razona. Las herramientas deterministas de Personal, Equipo e Incidentes son las que deciden `CUMPLE` / `NO_CUMPLE` con evidencia, y la evaluación demuestra que detectan las fallas inyectadas. P3 es dueño de esa verificación.

## What Changes

- Herramientas de Personal: disponibilidad en el turno, vigencia de certificaciones y doble asignación.
- Herramientas de Equipo: disponibilidad, estado y equivalentes solo en alternativas.
- `buscar_incidentes`: hasta 5 incidentes ordenados por nivel potencial.
- Agentes Personal y Equipo: convierten las herramientas en `ResultadoRequisito` con evidencia y traza.
- Script `evaluar` sobre `data/evaluacion.json`.

## Capabilities

### New Capabilities
- `verificacion-personal`: herramientas y agente de competencias y disponibilidad del personal.
- `verificacion-equipo`: herramientas y agente de estado y disponibilidad de equipos.
- `busqueda-incidentes`: consulta determinista de incidentes similares.
- `evaluacion`: script que mide la detección de fallas inyectadas.

### Modified Capabilities
<!-- Ninguna. -->

## Impact

- Código: `backend/app/tools/`, `backend/app/agents/personal.py`, `backend/app/agents/equipo.py`, `scripts/evaluar.py`, `backend/tests/`.
- Lo consume P2 (agentes y `buscar_incidentes`); usa `contract.py` (P1) y `data/evaluacion.json` (P4).
- Requisitos: RF-F1-13, 14, 15, 16, 19 · RF-F3-21, 23 · RT-01, RT-06.
