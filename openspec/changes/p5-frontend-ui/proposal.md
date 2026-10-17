## Why

El jurado ve CAPATAZ a través de la UI: los agentes trabajando en vivo, el semáforo de controles con su evidencia, las alternativas verificadas y la decisión humana. P5 es dueño de toda la interfaz y puede avanzar sin backend gracias a un replay escrito a mano.

## What Changes

- Proyecto Vite + React + TS + Tailwind + shadcn/ui con proxy `/api` y `VITE_API_URL`.
- Reductor único de eventos, cliente SSE con reconexión y reproductor de replays en el navegador.
- Pantallas: inicio de tarea, grafo vivo, semáforo, cajón de evidencia, conflicto y alternativas, comparación de planes, confirmación de campo, estado bloqueado, barra de decisión y línea de tiempo.
- Rotulado «Plan (PTW borrador)», insignias «simulado» y «Replay».
- Despliegue de vitrina en Vercel.

## Capabilities

### New Capabilities
- `ui-inicio-tarea`: presets, formulario libre y selector vivo/replay.
- `ui-ejecucion-en-vivo`: reductor de eventos, SSE, grafo de agentes, semáforo y evidencia.
- `ui-conflicto-y-decision`: alternativas, comparación, campo, bloqueo, decisión y línea de tiempo.
- `ui-despliegue`: frontend local para la demo y vitrina en Vercel.

### Modified Capabilities
<!-- Ninguna. -->

## Impact

- Código: `frontend/`, `replays/e1.json` provisional.
- Consume la API y los eventos acordados en `p1-contrato-api-runtime/design.md`.
- Requisitos: RF-F0-03, 13, 19 · RF-F1-30–36 · RF-F2-30–35 · RF-F3-03, 10, 12, 13, 14, 30, 43, 45, 46 · RT-07.
