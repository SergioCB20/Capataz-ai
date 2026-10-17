# Fase 2 — Conflicto, alternativas, campo y decisión humana (1:50 – 2:50)

**Objetivo:** completar los escenarios **E2** (la estrella de la demo), **E2c** y **E3**. Aquí está el valor diferencial: el sistema no solo dice «no», propone alternativas **verificadas** y se detiene cuando no hay una segura.

**Flujo B (conflicto):** primera pasada estricta → `NO_CUMPLE` en un control bloqueante → `conflicto.detectado` → el LLM propone alternativas → cada una se **re-verifica con herramientas** → hasta 2 rondas → plan.

## A. Detección y resolución de conflictos

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F2-01 | Si algún control bloqueante queda `NO_CUMPLE`, emitir `conflicto.detectado` con el control, el requisito y la causa (con su evidencia). El estado del run pasa a `RESOLVIENDO_CONFLICTO`. | M | PT, AP | E2: equipo requerido en `mantenimiento` ⇒ conflicto con evidencia del registro del equipo. |
| RF-F2-02 | **Generación de alternativas (LLM).** El Supervisor pide al LLM propuestas de `Cambio` de tipo `reprogramar_turno`, `equipo_equivalente` o `certificacion_equivalente`. El LLM solo puede referenciar IDs que existan en el catálogo. Emite `conflicto.alternativas`. | M | PT, IN | Test: alternativa con ID inexistente se descarta y se registra. |
| RF-F2-03 | **Verificación de cada alternativa con herramientas** (no con el LLM): se re-ejecutan Personal y Equipo sobre el plan modificado, ahora **permitiendo equivalencias**. Se emite `conflicto.alternativa_verificada` por alternativa con `cumple_bloqueantes`. | M | PT | Una alternativa que el LLM «cree» válida pero que falla la herramienta queda con `cumple_bloqueantes = false`. |
| RF-F2-04 | Máximo **2 rondas** (`Alternativa.ronda` ∈ {1, 2}). En la ronda 2 se informa al LLM de por qué fallaron las de la ronda 1. Tras la ronda 2 no se genera más. | M | PT | Test: ronda 3 imposible (validación del contrato + lógica del orquestador). |
| RF-F2-05 | Se descartan alternativas que eliminen un control o bajen su exigencia: una alternativa **no puede** quitar requisitos del catálogo. | M | AP | Test: alternativa con `Cambio` que omite un requisito ⇒ rechazada. |
| RF-F2-06 | Al menos una alternativa verificada ⇒ se arma el `Plan` con `estado_sistema` recalculado (`RECOMENDADO` o `REQUIERE_CAMPO`) y los `Cambio` aplicados, visibles. | M | AP, UX | E2 termina con plan `RECOMENDADO` que lista cada cambio frente al plan original. |
| RF-F2-07 | Ninguna alternativa verificada tras 2 rondas ⇒ plan `BLOQUEADO`, con motivo y **recomendación de escalamiento** (a quién avisar según el seed). Emite `plan.listo` y `humano.decision_requerida`. | M | AP, PT | E3 termina `BLOQUEADO` sin alternativas válidas. |
| RF-F2-08 | Cada alternativa lleva explicación en lenguaje claro generada por el LLM (por qué es razonable, qué se sacrifica), **separada** del veredicto determinista. | S | UX, IN | La UI muestra explicación y veredicto en campos distintos. |

## B. Condiciones de campo (E2c)

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F2-10 | Requisitos `condicion_campo` quedan `NO_VERIFICABLE`; si no hay incumplimientos bloqueantes, el plan es `REQUIERE_CAMPO` y se emite `humano.campo_requerido` con la lista de preguntas. | M | AP | E2c queda esperando campo (`ESPERANDO_CAMPO`). |
| RF-F2-11 | `POST /api/runs/{id}/campo` recibe `ConfirmacionesCampo` (con `usuario` y marca de tiempo). Se registra como evento `humano.campo_confirmado`, se recalcula el estado y, si procede, se pasa a `ESPERANDO_DECISION`. | M | AP, UX | Confirmar todas ⇒ `RECOMENDADO`. Responder «no se cumple» ⇒ `NO_CUMPLE` y flujo de conflicto. |
| RF-F2-12 | La confirmación de campo queda en la auditoría con quién y cuándo; no puede editarse (solo agregar otra). | S | AP | Los eventos son inmutables; la UI muestra la última confirmación vigente. |

## C. Decisión humana (reglas completas)

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F2-20 | **Plan `BLOQUEADO` solo admite rechazo.** `aprobar` sobre un plan bloqueado ⇒ 409, forzado en el backend, aunque el front lo permita por error. | M | AP, PT | Test de API: aprobar plan bloqueado devuelve 409 y no cambia el estado. |
| RF-F2-21 | Con varias alternativas verificadas, el humano elige cuál aprobar (`plan_id`). Las no elegidas quedan registradas como descartadas. | M | UX, AP | La decisión referencia el `plan_id` elegido. |
| RF-F2-22 | Rechazar exige comentario no vacío; el comentario se muestra en la línea de tiempo. | M | AP | Cubierto por el contrato (`DecisionHumana`); verificar el 422 en la API. |
| RF-F2-23 | Un run en estado terminal (`APROBADA`, `RECHAZADA`, `BLOQUEADA`, `ERROR`) no admite más decisiones ni confirmaciones. | M | PT | Test de transiciones de `EstadoRun`. |

## D. Frontend

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F2-30 | **Vista de conflicto:** el control en rojo con su causa y evidencia; las alternativas en tarjetas lado a lado, cada una con: cambios, veredicto (verificada ✓ / falló ✗ + motivo), explicación. | M | UX, IN | En E2 se ven ≥ 2 alternativas, al menos una verificada. |
| RF-F2-31 | **Comparación plan original vs. alternativa elegida:** diff visual de asignaciones (quién/qué equipo cambia y por qué). | M | UX, AP | El usuario identifica el cambio en < 5 s. |
| RF-F2-32 | **Formulario de confirmación de campo** (E2c): una pregunta por requisito, respuestas Sí/No + nota. | M | UX | Enviar actualiza el semáforo sin recargar. |
| RF-F2-33 | **Estado bloqueado (E3):** mensaje claro de por qué, escalamiento sugerido, y la barra de decisión solo ofrece «Rechazar» (con comentario). | M | UX, AP | El botón «Aprobar» no existe o está deshabilitado con explicación. |
| RF-F2-34 | **Línea de tiempo de auditoría:** lista cronológica de eventos clave (conflicto, alternativas, campo, decisión) con actor y hora. | M | AP, UX | Se puede recorrer E2 completo desde la línea de tiempo. |
| RF-F2-35 | Indicador de ronda de resolución (1/2, 2/2) durante el conflicto. | S | UX | Visible mientras `RESOLVIENDO_CONFLICTO`. |

## Criterios de salida de la fase

- [ ] E2, E2c y E3 funcionan de punta a punta con LLM real y con `fake`.
- [ ] Prueba de API: no se puede aprobar un plan bloqueado.
- [ ] Ninguna alternativa verificada depende del veredicto del LLM.
- [ ] Todos los eventos de E2 validan contra el contrato.

## Riesgos de la fase

| Riesgo | Mitigación |
|---|---|
| El LLM propone alternativas absurdas o con IDs inventados | Filtrado por catálogo (RF-F2-02) + verificación con herramientas (RF-F2-03). |
| E2 no resulta reproducible con LLM real | Grabar un `replay` de la mejor corrida (fase 3) y fijar semillas/temperatura baja. |
| Se complica la lógica de rondas | Implementar primero 1 ronda; la 2.ª es incremento (los tests de RF-F2-04 cubren el tope). |
