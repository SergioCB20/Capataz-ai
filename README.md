# CAPATAZ

Sistema multiagente que verifica, **antes** de ejecutar una tarea minera, que los controles críticos de seguridad pueden ejecutarse de verdad: personal competente, equipo disponible y en buen estado, y condiciones de campo. Propone la asignación de recursos más segura; **un humano siempre decide**.

> Proyecto de hackathon. Todos los datos son **simulados**: el prototipo demuestra la arquitectura, no una reducción real de accidentes.

## El problema

Muchos incidentes graves no ocurren porque falte un control, sino porque el control existe y no se ejecuta de forma efectiva (el ICMM lo identifica en la gestión de controles críticos). CAPATAZ revisa la *ejecutabilidad* del control antes de que empiece la tarea.

## Cómo funciona

1. Se registra una tarea (tipo, zona, turno).
2. El **Agente Riesgo** detecta peligros y los controles del catálogo que aplican.
3. El **Supervisor** reparte los requisitos al **Agente Personal** y al **Agente Equipo**, que trabajan en paralelo con herramientas deterministas.
4. Cada control queda en `CUMPLE`, `NO_VERIFICABLE` o `NO_CUMPLE` (gana el peor), y el plan en `RECOMENDADO`, `REQUIERE_CAMPO` o `BLOQUEADO`.
5. Si hay conflicto, se proponen alternativas (máx. 2 rondas) y **cada una se re-verifica con herramientas**.
6. La persona responsable aprueba o rechaza. Un plan bloqueado solo admite rechazo.

Principio central: **el código verifica; el LLM razona y explica.**

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Vite, React, TypeScript, Tailwind, shadcn/ui, React Flow, Motion, Zustand o `useReducer` |
| Tiempo real | SSE (`EventSource` en el front, `sse-starlette` en el backend); el stream queda abierto hasta `run.finalizado`/`run.error` |
| Backend | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, asyncio |
| Contrato → front | Pydantic → OpenAPI → `openapi-typescript` (`frontend/src/api/types.ts`) |
| LLM | SDK `anthropic` con *tool use* (`claude-sonnet-5-5`; `claude-haiku-5-5` opcional) |
| Persistencia | Supabase (Postgres) vía `supabase-py` async, con `MemoryStore` como respaldo |
| Pruebas | pytest |

## Estructura

```
capataz-project/
├─ backend/        FastAPI, contrato (contract.py), orquestador, agentes, herramientas
├─ frontend/       Vite + React + TS
├─ data/           Catálogo y escenarios (JSON, simulados)
├─ knowledge/      Base de conocimiento normativa (Markdown, con citas)
├─ replays/        Eventos grabados por escenario (demo sin red)
├─ registry/       Tarjetas de agentes (fase opcional, inspirada en NANDA)
├─ supabase/       Migraciones SQL
└─ docs/requisitos/  Requisitos funcionales por fase
```

## Arranque rápido

```bash
cp .env.example .env          # ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
# Sin credenciales: STORE_BACKEND=memory y LLM_MODE=fake

cd backend && uv sync && uv run uvicorn app.main:app --reload     # :8000
cd frontend && pnpm install && pnpm dev                           # proxy /api -> :8000
cd backend && uv run pytest                                       # pruebas
```

Las claves viven solo en el backend. Nunca se suben al repositorio.

## Escenarios de demo

| Id | Caso | Resultado |
|---|---|---|
| E1 | Caso limpio | `RECOMENDADO` |
| E2 | Equipo en mantenimiento y sin personal certificado; hay alternativas | `BLOQUEADO` → alternativa verificada → `RECOMENDADO` |
| E2c | Requisito de campo por confirmar | `REQUIERE_CAMPO` → confirmación |
| E3 | Sin alternativa segura | `BLOQUEADO`, solo rechazo |

Si falla la red o el LLM, la demo corre en **modo replay**.

## Documentación

Requisitos funcionales por fase, anexo de Supabase y matriz de trazabilidad con la rúbrica: [`docs/requisitos/00-indice.md`](docs/requisitos/00-indice.md).