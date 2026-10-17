## ADDED Requirements

### Requirement: Arranque sin credenciales
El backend SHALL arrancar con `STORE_BACKEND=memory` y `LLM_MODE=fake` sin claves, e informarlo en `GET /api/health` (RF-F0-05, RF-F0-07).

#### Scenario: Salud en modo memoria
- **WHEN** se llama `GET /api/health` con `STORE_BACKEND=memory`
- **THEN** responde 200 con `{store: "memory", llm_mode}`

### Requirement: Catálogo por API
`GET /api/catalogo` SHALL devolver el `Catalogo` completo, incluidos los incidentes (RF-F0-10).

#### Scenario: Catálogo válido
- **WHEN** se pide el catálogo
- **THEN** la respuesta valida contra `Catalogo.model_json_schema()`

### Requirement: Crear y consultar runs
`POST /api/runs` SHALL validar `RunCrear`, persistir el run en `EVALUANDO`, responder `RunCreado` en menos de 1 s y lanzar `ejecutar_run` en segundo plano; `GET /api/runs/{id}` SHALL devolver estado, plan y decisión (RF-F1-01, RF-F1-04).

#### Scenario: Run creado
- **WHEN** se envía `RunCrear` con `escenario_id = "E1"`
- **THEN** se devuelve un `run_id` y el run existe en el `Store`

### Requirement: Eventos en vivo por SSE
`GET /api/runs/{id}/eventos` SHALL reenviar primero los eventos persistidos desde `Last-Event-ID` y luego los nuevos, y SHALL quedar abierto con latidos hasta `run.finalizado` o `run.error`, también mientras espera a una persona (RF-F1-03).

#### Scenario: Recarga a mitad del run
- **WHEN** el cliente se reconecta con `Last-Event-ID = 5`
- **THEN** recibe los eventos desde `seq = 6` sin huecos

### Requirement: Decisión humana con reglas
`POST /api/runs/{id}/decision` SHALL aceptar solo runs en `ESPERANDO_DECISION`, rechazar con 409 la aprobación de un plan `BLOQUEADO` o una decisión duplicada, y con 422 un rechazo sin comentario (RF-F1-20, RF-F2-20, RF-F2-22, RF-F2-23, RT-04).

#### Scenario: Aprobar un plan bloqueado
- **WHEN** se envía `aprobar` sobre un plan `BLOQUEADO`
- **THEN** responde 409 y el estado del run no cambia

#### Scenario: Rechazo sin comentario
- **WHEN** se envía `rechazar` sin comentario
- **THEN** responde 422

### Requirement: Confirmación de campo
`POST /api/runs/{id}/campo` SHALL aceptar `ConfirmacionesCampo` solo en `ESPERANDO_CAMPO`, emitir `humano.campo_confirmado` y delegar el recálculo en `confirmar_campo` (RF-F2-11).

#### Scenario: Run terminal
- **WHEN** se envían confirmaciones a un run `APROBADA`
- **THEN** responde 409

### Requirement: CORS configurable
FastAPI SHALL aceptar solo los orígenes listados en `CORS_ORIGINS` (RF-F0-18).

#### Scenario: Origen no listado
- **WHEN** llega una petición desde un origen fuera de `CORS_ORIGINS`
- **THEN** la respuesta no incluye cabeceras CORS que la permitan
