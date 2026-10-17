# Fase 4 — Registro de agentes inspirado en NANDA (opcional)

**Condición de entrada:** se hace **solo después** de que los escenarios principales funcionan (criterios de salida de las fases 0, 1 y 2 cumplidos). Puede avanzar en paralelo a la fase 3 por una persona libre. **Corte duro: 3:30** — lo que no esté, no entra.

**Posicionamiento (honesto):** «inspirado en NANDA», no «implementamos NANDA». Apunta al reconocimiento opcional «mejor aplicación de NANDA» y refuerza el criterio de **Propuesta técnica** (agentes descubribles y verificables). No es dependencia de ningún escenario.

**Pendiente de verificar:** los nombres de campos de `AgentFacts` en el contrato siguen la idea de las *AgentFacts* de NANDA, pero **no se han contrastado con la especificación completa**. Revisar la documentación oficial antes de afirmar compatibilidad.

## Nivel 1 — Tarjetas y descubrimiento (≈ 30–40 min) · prioridad M dentro de la fase

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F4-01 | Una tarjeta `AgentFacts` por agente en `registry/*.json` (Supervisor, Riesgo, Personal, Equipo): `id` (`capataz:agente-…`), nombre, descripción, `endpoints`, formato de uso, `capabilities` (con modelos de entrada/salida), `security` (qué lee, `requires_human_approval`) y `certification`. | M | PT, IN | Las 4 tarjetas validan contra `AgentFacts`. |
| RF-F4-02 | Clase `Registry` que carga las tarjetas y permite buscar por capacidad (`verificar_personal`, `verificar_equipo`, …). | M | PT | Test: buscar `verificar_equipo` devuelve al Agente Equipo. |
| RF-F4-03 | El Supervisor **descubre** a qué agente enviar cada requisito consultando el registro por capacidad, en lugar de tener la asignación fija en código. | M | PT, IN | Quitar la tarjeta de Equipo hace que el requisito de equipo quede `NO_VERIFICABLE` (no `CUMPLE`). |
| RF-F4-04 | `GET /api/registro?capacidad=` devuelve las tarjetas. | M | EJ | Respuesta válida y filtrable. |
| RF-F4-05 | Panel «Agentes» en la UI: tarjeta por agente con capacidades, qué datos lee, requiere aprobación humana, estado de verificación. | M | UX, IN | Visible desde el grafo (clic en el nodo). |
| RF-F4-06 | Los eventos usan el `id` de la tarjeta como `actor` (ya definido en el contrato). | M | PT | La línea de tiempo muestra el id de la tarjeta. |
| RF-F4-07 | Persistir el registro en Supabase (tabla `agent_registry`) además de los JSON; los JSON son la fuente y la tabla un reflejo. | C | PT | Cargar el registro llena la tabla de forma idempotente. |

## Nivel 2 — Firma y verificación (≈ 1 h) · solo si el Nivel 1 está completo y sobra tiempo

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F4-10 | Cada tarjeta se **firma** (versión simplificada, sin DIDs ni *Verifiable Credentials*): firma sobre el JSON canónico con una clave del proyecto. | C | PT, IN | Las tarjetas incluyen firma y huella. |
| RF-F4-11 | El Supervisor verifica la firma antes de delegar; una tarjeta alterada se rechaza y se emite un evento de error visible. | C | PT, IN | Test: modificar un campo de la tarjeta ⇒ el agente no se invoca. |
| RF-F4-12 | La UI muestra «firma verificada ✓ / inválida ✗» por agente. | C | UX | Alterar una tarjeta en la demo muestra el rechazo. |
| RF-F4-13 | Dejar escrito que la clave es de demostración y que no hay raíz de confianza real. | M (si se hace N2) | AP | Nota en la pantalla «Acerca del sistema» o en el panel. |

## Nivel 3 — Fuera del MVP (solo mencionar como hoja de ruta)

- Exponer agentes por MCP/A2A para que otros sistemas los consuman.
- Índice/registro real y descubrimiento entre organizaciones.
- Identidad descentralizada y credenciales verificables reales.

## Criterios de salida

- [ ] Nivel 1: el Supervisor descubre agentes por capacidad y la UI lo muestra.
- [ ] Si se hizo el Nivel 2: demostrable la alteración de una tarjeta.
- [ ] **Ningún escenario principal depende de esta fase** (se puede desactivar con una variable y E1–E3 siguen funcionando).

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Consume tiempo de la fase 3 (demo/replay) | Corte duro a las 3:30; fase 3 tiene prioridad. |
| Sobreafirmar el alineamiento con NANDA | Texto del pitch: «inspirado en NANDA»; verificar campos con la especificación. |
| El descubrimiento dinámico introduce fallas | Bandera `USE_REGISTRY=false` vuelve a la asignación fija. |
