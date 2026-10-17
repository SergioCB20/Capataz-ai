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

## Acuerdos que P2 fija con P1, P3, P4 y P5

> Lo que el código de P2 ya hace y de lo que dependen los demás. Si algo de aquí no les sirve, avisen a P2 antes de cambiar su lado.

### Para todos: convenciones de planes y eventos

- **`Plan.id == Alternativa.id`** en cada plan alternativo. Es la única relación entre la tarjeta de una alternativa y su plan (el contrato no tiene otro campo).
- **`plan.listo`**: `plan` es el plan **original** (puede ser `BLOQUEADO`) y `planes_alternativos` son los planes de las alternativas verificadas, **el mejor primero** (primero `RECOMENDADO`, luego `REQUIERE_CAMPO`; a igualdad, menos cambios). Sin conflicto, `planes_alternativos` va vacío.
- **`humano.decision_requerida`**: `plan_id` es el del **mejor candidato** (`planes_alternativos[0]` si existe, si no `plan`). `solo_rechazo = true` cuando ese candidato no es `RECOMENDADO` y no hay nada que confirmar en campo.
- **Campo**: antes de `humano.campo_requerido` se emite `plan.listo` con el plan en `REQUIERE_CAMPO`. Tras `confirmar_campo` se emiten `supervisor.consolidado`, `plan.listo` (**mismo `Plan.id`**, resultados actualizados) y `humano.decision_requerida` (o de nuevo `campo_requerido` si quedan preguntas).
- **Estados**: solo se aprueba un plan `RECOMENDADO`. Un plan que no puede aprobarse y no tiene preguntas de campo (p. ej. un agente falló y quedó `NO_VERIFICABLE`) pide decisión con `solo_rechazo = true`.
- **Variables de entorno de P2** (todas opcionales): `LLM_MODE` (`fake` por defecto), `LLM_MODEL`, `OPENROUTER_API_KEY`, `LLM_BASE_URL`, `LLM_TIMEOUT_S`, `LLM_TEMPERATURE`, `AGENTE_TIMEOUT_S` (30), `RIESGO_TIMEOUT_S` (45), `KNOWLEDGE_DIR`.

### P1

- `GET /api/health` devuelve `orquestador: "p2"` en cuanto existe `agents/supervisor.py`.
- **Dependencia faltante en `pyproject.toml`: `openai`** (cliente de OpenRouter). Sin ella, `LLM_MODE=real` falla con «Falta el paquete `openai`»; el modo `fake` no la necesita.
- `ejecutar_run` y `confirmar_campo` aceptan un argumento opcional `deps=` (solo para pruebas); P1 los llama con la firma acordada.
- Con los sustitutos de P3 todo queda `NO_VERIFICABLE`, así que el Supervisor real **no permite aprobar E1** hasta que P3 entregue. Por eso `tests/test_api.py` fija el orquestador sustituto de P1 en su fixture `client` (esas pruebas cubren la API, no la orquestación).
- Un `emitir` con payload inválido lanza error y el run termina en `run.error`; P2 emite siempre payloads válidos contra `PAYLOAD_POR_TIPO` (las pruebas de P2 validan cada evento).

### P3

- **P2 emite `agente.iniciado` y `agente.completado` de Personal y Equipo** (actores `ACTOR_PERSONAL`, `ACTOR_EQUIPO`), solo en la primera pasada. **P3 emite únicamente `agente.herramienta`** (uno por llamada a herramienta, con `TraceHerramienta`).
- Las firmas son las acordadas. P2 las importa desde `agents/_p3.py`: usa `app.agents.personal`, `app.agents.equipo` y `app.tools.incidentes` apenas existan; si un módulo existe pero falla al importarse, el error **se propaga** (no se oculta con el stub).
- **Verificar contra `sol.tarea`, no contra el catálogo original.** Al evaluar una alternativa, P2 llama de nuevo a los agentes con una `Tarea` modificada y `permitir_equivalencias=True`:
  - `equipo_equivalente` sustituye un ID en `sol.tarea.asignacion.equipos`;
  - `certificacion_equivalente` sustituye un ID en `sol.tarea.asignacion.personas`;
  - `reprogramar_turno` cambia `sol.tarea.turno` (la asignación no cambia).
  La disponibilidad, la vigencia de certificaciones y el mantenimiento deben evaluarse contra ese turno y esa asignación.
- Devolver un `ResultadoRequisito` por cada requisito pedido, con `control_id` y `requisito_id` correctos. Los resultados que P2 no pidió se ignoran; los que falten quedan `NO_VERIFICABLE`.
- Si un agente lanza excepción o tarda más de `AGENTE_TIMEOUT_S`, P2 deja sus requisitos `NO_VERIFICABLE` y el run sigue.
- `buscar_incidentes(catalogo, equipo=None, actividad=None, riesgo_critico=None, limite=5)` se llama **con argumentos con nombre**. El Agente Riesgo (en modo fake) pasa `actividad = nombre del tipo de tarea` y `riesgo_critico = nombre del peligro` en texto libre; el LLM real puede pasar textos distintos, así que conviene una coincidencia tolerante (minúsculas, sin tildes, por contención).
- Las equivalencias de personas/equipos que P3 reconozca deben salir de `Requisito.certificaciones_equivalentes` y `Equipo.tipos_equivalentes`.

### P4

- **El tipo de tarea no declara peligros.** El Agente Riesgo deduce los peligros de un tipo de tarea a partir de los controles: un control aplica si `tipo_tarea ∈ Control.aplica_a`, y su peligro es `Control.peligro_id`. Todo control con `aplica_a` correcto queda **siempre exigido**, aunque el LLM no lo mencione.
- **`Escenario.escalamiento`** es el texto que se muestra tal cual cuando el plan queda sin alternativa segura (E3, y cualquier escenario que termine bloqueado). Sin él se usa un texto genérico.
- **Diseño de E2:** para que exista una alternativa verificable, el catálogo debe contener, además de lo asignado en la tarea, otro equipo (mismo `tipo_equipo` o con `tipos_equivalentes` que lo cubran) y otra persona con la certificación vigente a la fecha del turno. P2 solo propone sustituciones de IDs que existan; no inventa recursos.
- **Formato de turno en alternativas:** `AAAA-MM-DD/dia` o `AAAA-MM-DD/noche`. `Persona.turnos` (disponibilidad) y `Equipo.mantenimiento` (no disponibilidad) se usan al reprogramar.
- **E1 limpio:** sus controles no deben incluir requisitos `condicion_campo` si se espera `RECOMENDADO`. Un control con requisitos de equipo y de campo a la vez es válido, pero el resultado será `REQUIERE_CAMPO` hasta confirmar.
- Si un escenario mezcla un conflicto y un requisito de campo, las alternativas verificadas quedan `REQUIERE_CAMPO` y el flujo pasa por `humano.campo_requerido` antes de la decisión.
- **`Incidente.control_fallido`** debe ser el ID de un control del catálogo: es lo que permite sumar controles extra (checklist dinámico). Un ID inexistente se descarta.
- **`knowledge/*.md`**: se carga en el contexto del Agente Riesgo (solo archivos `.md`, hasta 12 000 caracteres, en orden alfabético). Incluir en cada documento su fuente y referencia.
- Las respuestas del modo fake se eligen por `Run.escenario_id`; los IDs de escenario esperados son `E1`, `E2`, `E2c` y `E3`.

### P5

- Secuencia de E1: `run.iniciado` → Riesgo (`agente.iniciado`, `agente.herramienta`×n, `agente.completado`) → Personal y Equipo en paralelo (sus `iniciado`/`completado` pueden intercalarse) → `supervisor.consolidado` → `plan.listo` → `humano.decision_requerida`.
- **Conflicto:** `conflicto.detectado` se emite **una vez por requisito** que falla; luego, por cada ronda (1 y 2), `conflicto.alternativas` y un `conflicto.alternativa_verificada` por alternativa, con `cumple_bloqueantes`, `motivo_fallo` (veredicto de las herramientas) y `explicacion` (del LLM) en campos separados. La ronda es `ronda` del evento. Una ronda sin propuestas válidas no emite `conflicto.alternativas`.
- Durante la re-verificación de alternativas llegan `agente.herramienta` de Personal/Equipo **sin** un `agente.iniciado` previo (P2 no vuelve a anunciar a los agentes en las alternativas): el reductor debe tolerarlo.
- `ResultadoControl` no trae nombre ni fuente: unirlos por `control_id` con `Catalogo.controles` (`nombre`, `fuente`, `bloqueante`).
- Un plan alternativo se relaciona con su tarjeta por `Plan.id == Alternativa.id`. El plan original (`plan`) se muestra como «antes» y su `motivo` explica el bloqueo; `Plan.escalamiento` solo viene cuando no hay alternativa segura.
- `humano.campo_requerido` trae las preguntas por `requisito_id`. Tras la confirmación llega un `plan.listo` nuevo con el **mismo `Plan.id`**.
- Cada alternativa tiene `cambios` de tipo `reprogramar_turno` (`desde`/`hacia` son turnos `AAAA-MM-DD/dia|noche`), `equipo_equivalente` (IDs de equipo) o `certificacion_equivalente` (IDs de persona); para el diff de asignaciones comparar `plan.asignacion` del original con el de la alternativa.
- Los textos de `Plan.motivo`, `Alternativa.explicacion`, `motivo_fallo` y los `resumen` de agentes ya vienen en español.
