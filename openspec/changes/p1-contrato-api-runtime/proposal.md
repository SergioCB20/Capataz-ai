## Why

Los otros cuatro frentes (agentes, herramientas, datos y UI) necesitan un contrato de datos común y un backend que ejecute runs, persista eventos y los transmita en vivo. P1 es dueño de ese «esqueleto» y debe publicarlo primero para que nadie quede bloqueado.

## What Changes

- `backend/app/contract.py` con todos los modelos, enums, eventos, `PAYLOAD_POR_TIPO`, `validar_payload`, `consolidar_control` y `calcular_estado_sistema`, más sus tests.
- Interfaz `Store` y `MemoryStore` (con volcado JSONL).
- API FastAPI: salud, catálogo, crear run, consultar run, SSE de eventos, decisión humana, confirmación de campo, CORS.
- Máquina de estados de `EstadoRun` y reglas de decisión (bloqueado solo admite rechazo).
- Modo replay en el backend y comando para grabar replays.
- `.env.example` y README de arranque.

## Capabilities

### New Capabilities
- `contrato-datos`: modelos Pydantic, eventos y funciones de consolidación compartidas por todo el sistema.
- `api-runs`: endpoints HTTP, SSE, decisión humana, confirmación de campo y CORS.
- `persistencia-eventos`: interfaz `Store`, `MemoryStore` y reglas de auditoría por eventos.
- `modo-replay`: grabación y reproducción de runs sin LLM ni red.

### Modified Capabilities
<!-- Ninguna: no hay specs previas. -->

## Impact

- Código: `backend/app/contract.py`, `backend/app/api/`, `backend/app/store/base.py`, `backend/app/store/memory.py`, `scripts/grabar_replay.py`, `.env.example`.
- Lo consumen P2 (emite eventos), P3 (modelos de verificación), P4 (`SupabaseStore` implementa `Store`) y P5 (tipos TS, SSE).
- Requisitos: RF-F0-02, 05, 06, 07, 10, 18 · RF-F1-01–04, 20, 21 · RF-F2-11 (endpoint), 20, 22, 23 · RF-F3-01, 02, 05 · RT-02–05, RT-08, RT-09.
