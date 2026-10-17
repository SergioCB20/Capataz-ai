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
6. El resultado se presenta como **«Plan (PTW borrador)»**. La persona responsable aprueba o rechaza; un plan bloqueado solo admite rechazo. CAPATAZ entrega un borrador: la persona lo firma, el código no firma ni autoriza.

Principio central: **el código verifica; el LLM razona y explica.**

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Vite, React, TypeScript, Tailwind, shadcn/ui, React Flow |
| Tiempo real | SSE (`EventSource`) |
| Backend | Python 3.11+, FastAPI, Pydantic v2, asyncio |
| LLM | GPT-6 Luna vía OpenRouter (API compatible con OpenAI, *function calling*) |
| Persistencia | Supabase (Postgres), con `MemoryStore` como respaldo |
| Pruebas | pytest |

## Estructura

```
capataz/
├─ backend/        FastAPI, contrato (contract.py), orquestador, agentes, herramientas
├─ frontend/       Vite + React + TS
├─ data/           Catálogo, incidentes y escenarios (JSON, simulados)
├─ knowledge/      Base de conocimiento normativa (Markdown, con citas)
├─ replays/        Eventos grabados por escenario (demo sin red)
├─ registry/       Tarjetas de agentes (futuro, vacía en el MVP)
├─ scripts/        Generador sintético (borradores de datos, revisión humana)
├─ supabase/       Migraciones SQL
├─ docs/requisitos/   Requisitos funcionales por fase
└─ docs/arquitectura/ Diagrama de arquitectura y notas
```

## Arranque rápido

```bash
cp .env.example .env          # OPENROUTER_API_KEY, LLM_MODEL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL, CORS_ORIGINS
# Sin credenciales: STORE_BACKEND=memory y LLM_MODE=fake

cd backend && uv sync && uv run uvicorn app.main:app --reload     # :8000
cd frontend && pnpm install && pnpm dev                           # proxy /api -> :8000
cd backend && uv run pytest                                       # pruebas
```

Las claves viven solo en el backend. Nunca se suben al repositorio.

### Despliegue y demo

- **Demo:** frontend y backend **locales**, para no depender de Internet:
  ```bash
  cd frontend && VITE_API_URL=http://localhost:8000 pnpm build && pnpm preview
  ```
  El backend debe incluir ese origen en `CORS_ORIGINS`.
- **Vercel:** solo vitrina pública del frontend (`VITE_API_URL` apunta al backend local); no se usa para presentar. Una página HTTPS que llama a `http://localhost` puede ser bloqueada por el navegador: verificar antes de la demo.
- **SSE:** sale del backend local, no pasa por Vercel.

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

Arquitectura: [`docs/arquitectura/README.md`](docs/arquitectura/README.md).