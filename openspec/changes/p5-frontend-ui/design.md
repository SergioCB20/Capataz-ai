## Context

P5 no espera al backend: escribe `replays/e1.json` a mano con los tipos de evento y payloads de los acuerdos de interfaz (`p1-contrato-api-runtime/design.md`) y desarrolla toda la UI contra ese archivo. Cuando el backend está listo, solo cambia la fuente de eventos.

## Goals / Non-Goals

**Goals:**
- Una sola lógica de estado para vivo y replay.
- UI clara para el jurado en menos de 5 minutos de demo.

**Non-Goals:**
- Login, historial y métricas (recortables, RF-F3-15, 16, 31).
- Panel de agentes NANDA (hoja de ruta).

## Decisions

- **Reductor puro `reducir(estado, evento)`.** Toda la UI se deriva del arreglo de eventos; recargar o reproducir da el mismo resultado (RF-F1-35).
- **Fuente de eventos intercambiable.** `fuenteSSE(runId)` y `fuenteArchivo(json, velocidad)` exponen la misma interfaz `onEvento`; el replay en el navegador sirve también para la vitrina de Vercel sin backend (RF-F3-46).
- **Tipos TS primero a mano, luego generados.** Mientras P1 no expone el OpenAPI, tipos escritos a mano según los acuerdos; después `openapi-typescript` (RF-F0-03).
- **Componentes de shadcn/ui** para tarjetas, botones, cajón (`Sheet`) y diálogos, y React Flow para el grafo con 4 nodos fijos.
- **Estado nunca solo por color:** icono + texto en cada estado (RF-F1-32, RF-F3-13).

## Risks / Trade-offs

- [El replay a mano difiere del real] → Usar exactamente la tabla de eventos acordada y validar contra el primer run real a las 15:45.
- [Demasiadas pantallas para una persona] → Orden de entrega: E1 (inicio, grafo, semáforo, evidencia, decisión) → E2 (alternativas, comparación) → E2c/E3 → pulido. P1 apoya tras el hito de 16:20.
- [Vercel no alcanza `localhost`] → La demo usa el frontend local; Vercel solo es vitrina.
