## Context

P2 trabaja contra los acuerdos de interfaz de `p1-contrato-api-runtime/design.md`. No espera a nadie: usa stubs de P3 y la función `emitir` que le pasa P1.

## Goals / Non-Goals

**Goals:**
- `ejecutar_run` y `confirmar_campo` funcionando con `LLM_MODE=fake` para E1–E3.
- El LLM solo razona, propone y explica; nunca decide un `CUMPLE` (RT-01).

**Non-Goals:**
- Herramientas deterministas (P3), API y persistencia (P1), datos (P4).

## Decisions

- **Orquestador asyncio propio, sin LangGraph.** Es un flujo corto y fijo; un framework añade más riesgo que valor en 2 h.
- **Stubs primero.** `agents/_stubs.py` con `verificar_personal`, `verificar_equipo` y `buscar_incidentes` que devuelven `NO_VERIFICABLE` o listas vacías; se reemplazan por los de P3 con un cambio de `import`.
- **Modo fake por agente.** El cliente devuelve respuestas fijas por nombre de agente y escenario, para que E1–E3 corran sin red y sean reproducibles en tests y replays.
- **Filtrado por catálogo después del LLM.** Todo ID que proponga el LLM (control, incidente, persona, equipo) se valida contra el catálogo; lo inválido se descarta y se registra.
- **Supervisor determinista.** Derivar requisitos, repartirlos y decidir rondas es código; el LLM solo interviene en Riesgo, alternativas, explicaciones y resumen.

## Flujo de `ejecutar_run`

1. `run.iniciado` → Agente Riesgo (`EvaluacionRiesgo`, con `buscar_incidentes` como herramienta).
2. Supervisor: controles → `RequisitoAVerificar`; `competencia` → Personal, `equipo` → Equipo, `condicion_campo` → `NO_VERIFICABLE`.
3. `asyncio.gather(verificar_personal, verificar_equipo)` con `permitir_equivalencias = False`.
4. `consolidar_control` + `calcular_estado_sistema` → `supervisor.consolidado`.
5. Si hay bloqueante `NO_CUMPLE`: `conflicto.detectado` → ronda 1 de alternativas → re-verificar cada una con `permitir_equivalencias = True` → si ninguna pasa, ronda 2 con los motivos de fallo → si ninguna pasa, plan `BLOQUEADO` con escalamiento.
6. Si es `REQUIERE_CAMPO`: `humano.campo_requerido`. Si no: `plan.listo` + `humano.decision_requerida`.

## Risks / Trade-offs

- [El LLM devuelve JSON inválido] → Validar con Pydantic, un reintento y, si falla, `NO_VERIFICABLE` o `run.error` (RF-F1-06).
- [E2 no es reproducible con el LLM real] → Temperatura baja y grabar el replay de la mejor corrida.
- [P3 se atrasa] → Los stubs permiten llegar al hito de E1 con estados `NO_VERIFICABLE`.
