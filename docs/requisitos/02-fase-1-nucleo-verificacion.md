# Fase 1 — Núcleo de verificación: Escenario 1 de punta a punta (0:40 – 1:50)

**Objetivo:** ejecutar el caso limpio (E1) desde el formulario hasta la aprobación, con agentes reales, eventos en vivo y evidencia. Al terminar existe el **esqueleto vertical completo**; las fases siguientes agregan casos, no capas.

**Flujo:** tarea → Riesgo → Supervisor deriva requisitos → Personal ‖ Equipo (en paralelo) → consolidación → plan `RECOMENDADO` → decisión humana.

## A. Backend: ejecución y eventos

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F1-01 | `POST /api/runs` valida `RunCrear`, crea la `Tarea`, persiste el `Run` en estado `EVALUANDO` y devuelve `RunCreado`. La ejecución corre en segundo plano. | M | EJ | Respuesta < 1 s; el run existe en el `Store`. |
| RF-F1-02 | Todo evento es un `Evento` con `seq` monótono por run, `actor` = id del agente (`capataz:agente-…`) o `sistema`, y `payload` válido según `PAYLOAD_POR_TIPO`. Se persiste **antes** de emitirse. | M | PT | `validar_payload()` pasa para todos los eventos de E1; `seq` sin huecos. |
| RF-F1-03 | `GET /api/runs/{id}/eventos` es un stream SSE: primero reenvía lo persistido (desde `Last-Event-ID` o `seq` dado) y luego los nuevos. Cierra tras `run.finalizado`/`run.error` o al quedar esperando humano sin más trabajo. | M | EJ, UX | Recargar la página a mitad de un run reconstruye el mismo estado. |
| RF-F1-04 | `GET /api/runs/{id}` devuelve el `Run` con estado, plan vigente y decisión (si existe). | M | EJ | Coherente con el último evento. |
| RF-F1-05 | Secuencia de eventos de E1: `run.iniciado` → `agente.iniciado`/`agente.herramienta`/`agente.completado` (Riesgo) → ídem Personal y Equipo → `supervisor.consolidado` → `plan.listo` → `humano.decision_requerida`. | M | PT | Test de integración compara tipos y orden (con LLM en modo `fake`). |
| RF-F1-06 | Fallo de un agente (excepción, *timeout*, salida inválida): se emite `run.error` o el agente devuelve `NO_VERIFICABLE` para sus requisitos; **nunca** `CUMPLE` por omisión. El run no queda colgado. | M | PT | Test: agente que lanza excepción ⇒ estado `ERROR` o requisito `NO_VERIFICABLE`. |
| RF-F1-07 | Límite de tiempo por agente y total por run (configurables). | S | EJ | Run de E1 termina < 30 s con LLM real. |

## B. Agentes y herramientas

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F1-10 | **Agente Riesgo.** Entrada: tarea. Salida: `EvaluacionRiesgo` con `PeligroDetectado` y los controles del catálogo aplicables (`aplica_a` ∋ tipo de tarea). El LLM razona sobre peligros y justifica con la base de conocimiento; los **IDs de control salen del catálogo**, no se inventan. | M | PT, AP | Test: IDs devueltos ⊆ catálogo; descripción de tarea ambigua no produce controles inexistentes. |
| RF-F1-11 | **Supervisor/orquestador** (asyncio propio). Convierte controles en `RequisitoAVerificar`; los requisitos `competencia` van al Agente Personal, `equipo` al Agente Equipo; `condicion_campo` queda `NO_VERIFICABLE` en la primera pasada. | M | PT | Cada requisito de cada control aparece exactamente una vez en un `AgenteSolicitud`. |
| RF-F1-12 | Personal y Equipo corren **en paralelo** (`asyncio.gather`). | M | PT, EJ | Test con retardo simulado: tiempo total ≈ máx, no suma. |
| RF-F1-13 | **Herramientas de Personal** (deterministas): listar personal disponible en un `TurnoRef`; verificar vigencia de cada `Certificacion` a la fecha del turno; detectar doble asignación en el mismo turno. | M | PT | Pruebas unitarias con datos del seed (certificación vencida ⇒ no cuenta). |
| RF-F1-14 | **Herramientas de Equipo** (deterministas): disponibilidad en el turno; `EstadoEquipo` (`operativo`/`mantenimiento`/`fuera_servicio`); tipo requerido y, solo en alternativas, equivalentes. | M | PT | Pruebas unitarias; primera pasada ignora `tipos_equivalentes`. |
| RF-F1-15 | Cada llamada a herramienta genera `TraceHerramienta` (nombre, entrada, salida resumida, duración) y un evento `agente.herramienta`. | M | UX, PT | La UI puede listar las herramientas usadas por cada agente. |
| RF-F1-16 | Cada `ResultadoRequisito` lleva `Evidencia` (registro consultado, campo, valor) y `verificado_por`. Sin evidencia ⇒ no puede ser `CUMPLE`. | M | AP, PT | Test: resultado `CUMPLE` sin evidencia es rechazado por la capa de agentes. |
| RF-F1-17 | Consolidación con `consolidar_control` y `calcular_estado_sistema` del contrato; evento `supervisor.consolidado` con los `ResultadoControl`. | M | PT | No existe lógica duplicada de «peor estado» fuera del contrato. |
| RF-F1-18 | Generación del `Plan` (`Asignacion` de personas y equipos) con `estado_sistema`. Si es `RECOMENDADO`, emite `plan.listo` y `humano.decision_requerida`. | M | AP | E1 produce un plan sin cambios (`Cambio` vacío). |
| RF-F1-19 | **Herramienta de Riesgo `buscar_incidentes(tipo_tarea, actividad, tipo_equipo)`** (determinista) sobre los incidentes del catálogo (RF-F0-16). El Agente Riesgo puede citar incidentes en su justificación, pero solo por IDs devueltos por la herramienta. | S | AP, PT | Test: IDs de incidentes citados ⊆ resultado de la herramienta. |

## C. Decisión humana (camino feliz)

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F1-20 | `POST /api/runs/{id}/decision` recibe `DecisionHumana`; valida que el plan exista y el run esté en `ESPERANDO_DECISION`. `aprobar` ⇒ `APROBADA`; `rechazar` (con comentario) ⇒ `RECHAZADA`. Emite `humano.decision_tomada` y `run.finalizado`. | M | AP, UX | Decisión duplicada ⇒ 409. Rechazo sin comentario ⇒ 422. |
| RF-F1-21 | Decisión y plan se guardan en el `Store` (tablas `planes`, `decisiones`). | M | EJ | Tras reiniciar el backend con Supabase, el run aprobado sigue consultable. |

## D. Frontend

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F1-30 | **Pantalla de inicio de tarea:** *presets* de escenario (E1, E2, E2c, E3) que rellenan el formulario, más modo libre (tipo de tarea, descripción, zona, turno). Selector de modo `vivo`/`replay`. | M | UX | Un clic en «Escenario 1» + «Evaluar» inicia el run. |
| RF-F1-31 | **Grafo vivo de agentes** (React Flow): nodos Supervisor, Riesgo, Personal, Equipo; estado de cada uno (inactivo/trabajando/completado/error) según eventos SSE; herramientas invocadas visibles. | M | UX, PT, IN | Se ve a Personal y Equipo trabajando a la vez. |
| RF-F1-32 | **Panel de controles** con semáforo: cada control y requisito con icono **y** texto (`CUMPLE`/`NO_VERIFICABLE`/`NO_CUMPLE`), indicando si es bloqueante. Insignia «simulado» según `Fuente`. | M | UX, AP | Legible sin depender del color (accesibilidad). |
| RF-F1-33 | **Cajón de evidencia:** al elegir un requisito se muestra su `Evidencia`, el agente que lo verificó y la fuente (normativa/guía/simulado). | M | UX, PT | Todo `CUMPLE` muestra al menos una evidencia. |
| RF-F1-34 | **Barra de decisión:** botones Aprobar/Rechazar; Rechazar abre campo de comentario obligatorio. Muestra el estado del plan. | M | UX, AP | Aprobar E1 cierra el run y lo refleja en la UI. |
| RF-F1-35 | Estado de la UI derivado de un reductor sobre los eventos (misma lógica en vivo y en *replay*). | M | EJ | Reproducir los eventos guardados deja la UI idéntica. |
| RF-F1-36 | Estados vacío, cargando y error visibles (sin pantallas en blanco si SSE se cae; reconexión automática). | S | UX | Cortar la red 5 s y restaurarla reanuda el stream. |

## Criterios de salida de la fase

- [ ] E1 corre de punta a punta con LLM real y con `fake`.
- [ ] La UI muestra grafo, semáforo, evidencia y decisión.
- [ ] Todos los eventos persisten y el run se reconstruye al recargar.
- [ ] Tests de herramientas y de integración de E1 en verde.

## Riesgos de la fase

| Riesgo | Mitigación |
|---|---|
| El LLM devuelve estructuras inválidas | Salida con *function calling* validada por Pydantic; un reintento; si falla ⇒ RF-F1-06. |
| Frontend bloqueado esperando al backend | Desarrollar contra eventos grabados del contrato (preparar ya un `replays/e1.json` a mano). |
| Latencia alta del LLM | Modelo más ligero de OpenRouter para tareas simples (cambiando `LLM_MODEL`, opcional); *timeouts* (RF-F1-07). |
