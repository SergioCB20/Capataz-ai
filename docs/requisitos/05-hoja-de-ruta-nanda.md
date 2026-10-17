# Hoja de ruta — Registro de agentes inspirado en NANDA

> **Estado: FUERA DEL ALCANCE del hackatón. No se implementa. Se conserva como idea de evolución del proyecto.**
>
> Todos los requisitos de este archivo tienen prioridad **F** (futuro). No cuentan en los recuentos M/S/C ni aparecen en la demo, el pitch ni la UI.

**Posicionamiento (honesto):** «inspirado en NANDA», no «implementamos NANDA». La idea es que los agentes sean descubribles y verificables. Ningún escenario depende de esto.

**Pendiente de verificar:** los nombres de campos de `AgentFacts` siguen la idea de las *AgentFacts* de NANDA, pero **no se han contrastado con la especificación completa**. Revisar la documentación oficial antes de afirmar compatibilidad.

## Nivel 1 — Tarjetas y descubrimiento

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F4-01 | Una tarjeta `AgentFacts` por agente en `registry/*.json` (Supervisor, Riesgo, Personal, Equipo): `id` (`capataz:agente-…`), nombre, descripción, `endpoints`, formato de uso, `capabilities` (con modelos de entrada/salida), `security` (qué lee, `requires_human_approval`) y `certification`. | F | PT, IN | Las 4 tarjetas validan contra `AgentFacts`. |
| RF-F4-02 | Clase `Registry` que carga las tarjetas y permite buscar por capacidad (`verificar_personal`, `verificar_equipo`, …). | F | PT | Test: buscar `verificar_equipo` devuelve al Agente Equipo. |
| RF-F4-03 | El Supervisor **descubre** a qué agente enviar cada requisito consultando el registro por capacidad, en lugar de tener la asignación fija en código. | F | PT, IN | Quitar la tarjeta de Equipo hace que el requisito de equipo quede `NO_VERIFICABLE` (no `CUMPLE`). |
| RF-F4-04 | `GET /api/registro?capacidad=` devuelve las tarjetas. | F | EJ | Respuesta válida y filtrable. |
| RF-F4-05 | Panel «Agentes» en la UI: tarjeta por agente con capacidades, qué datos lee, requiere aprobación humana, estado de verificación. | F | UX, IN | Visible desde el grafo (clic en el nodo). |
| RF-F4-06 | Los eventos usan el `id` de la tarjeta como `actor` (ya definido en el contrato). | F | PT | La línea de tiempo muestra el id de la tarjeta. |
| RF-F4-07 | Persistir el registro en Supabase (tabla `agent_registry`) además de los JSON; los JSON son la fuente y la tabla un reflejo. | F | PT | Cargar el registro llena la tabla de forma idempotente. |

## Nivel 2 — Firma y verificación

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F4-10 | Cada tarjeta se **firma** (versión simplificada, sin DIDs ni *Verifiable Credentials*): firma sobre el JSON canónico con una clave del proyecto. | F | PT, IN | Las tarjetas incluyen firma y huella. |
| RF-F4-11 | El Supervisor verifica la firma antes de delegar; una tarjeta alterada se rechaza y se emite un evento de error visible. | F | PT, IN | Test: modificar un campo de la tarjeta ⇒ el agente no se invoca. |
| RF-F4-12 | La UI muestra «firma verificada ✓ / inválida ✗» por agente. | F | UX | Alterar una tarjeta muestra el rechazo. |
| RF-F4-13 | Dejar escrito que la clave es de demostración y que no hay raíz de confianza real. | F | AP | Nota en la pantalla «Acerca del sistema» o en el panel. |

## Nivel 3 — Más adelante

- Exponer agentes por MCP/A2A para que otros sistemas los consuman.
- Índice/registro real y descubrimiento entre organizaciones.
- Identidad descentralizada y credenciales verificables reales.

## Riesgos (si se retoma)

| Riesgo | Mitigación |
|---|---|
| Sobreafirmar el alineamiento con NANDA | Decir «inspirado en NANDA»; verificar campos con la especificación. |
| El descubrimiento dinámico introduce fallas | Bandera `USE_REGISTRY=false` vuelve a la asignación fija. |
