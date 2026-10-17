# CAPATAZ

## La idea

Sistema multiagente para minería que verifica, **antes** de ejecutar una tarea, que los controles críticos de seguridad realmente pueden ejecutarse (personal competente, equipo disponible y en buen estado, condiciones de campo) y propone la asignación de recursos más segura. **Un humano siempre decide.**

Proyecto de hackatón (~5 h) con datos **simulados**: demuestra la arquitectura, no una reducción real de accidentes.

## El problema

En minería no faltan reglas: falla el momento en que se ejecuta la tarea. En 19 de 26 incidentes fatales analizados por el ICMM en 2025, el control existía pero no se ejecutó de forma efectiva. La barrera estaba definida y no funcionó en el momento crítico.

Límite honesto: el problema está respaldado por datos; **esta solución aún no está validada** con gente de planificación o seguridad minera.

## La solución

Dada una tarea planificada (tipo, zona, turno):

1. **Riesgo** detecta peligros y los controles del catálogo que aplican.
2. El **Supervisor** reparte los requisitos a **Personal** y **Equipo**, que verifican en paralelo con herramientas deterministas.
3. Cada control queda `CUMPLE`, `NO_VERIFICABLE` o `NO_CUMPLE` (gana el peor); el plan queda `RECOMENDADO`, `REQUIERE_CAMPO` o `BLOQUEADO`.
4. Si hay conflicto (p. ej. equipo en mantenimiento y sin personal certificado ese turno), se proponen alternativas (máx. 2 rondas) y cada una se re-verifica con herramientas.
5. Una persona aprueba o rechaza. Un plan bloqueado solo admite rechazo.

Principio: **el código verifica; el LLM razona y explica.** Nunca decide un `CUMPLE`.

Todo paso se emite como evento tipado, que sirve de auditoría. Los datos están definidos en `backend/app/contract.py`, que es la fuente de verdad.

## Stack (resumen; detalle en `README.md`)

Frontend: Vite + React + TS, Tailwind, shadcn/ui, React Flow, Motion. Tiempo real: SSE. Backend: Python 3.11+, FastAPI, Pydantic v2, asyncio. LLM: GPT-6 Luna vía OpenRouter (API compatible con OpenAI, function calling). Persistencia: Supabase vía `supabase-py` (async) con `MemoryStore` de respaldo. Entorno: `uv` + `pnpm`, sin Docker.

## Dónde está cada cosa

- `docs/requisitos/00-indice.md`: índice, reglas transversales (RT-01..10) y escenarios E1, E2, E2c, E3. Las fases `01`..`05`, el anexo de Supabase (`90`) y la matriz de trazabilidad (`91`) cuelgan de ahí.
- `docs/capataz-stack-y-contrato.html`: stack y contrato de datos. `docs/capataz-arquitectura.html`: diagramas y flujos.
- `docs/reparto-equipo.md` y `openspec/changes/p1`..`p5`: reparto entre 5 personas, hitos y tareas. Los acuerdos de interfaz entre personas están en `openspec/changes/p1-contrato-api-runtime/design.md`. Las convenciones de planes y eventos que P2 fija para P1, P3, P4 y P5 están en `openspec/changes/p2-orquestador-agentes-llm/design.md` (sección «Acuerdos que P2 fija…»).
- Si dos documentos se contradicen, mandan los requisitos (`docs/requisitos/`) y el contrato (`contract.py`); corrige el otro documento.

## Reglas de trabajo

- **Contrato primero:** `contract.py` es la única fuente de verdad. Si un requisito choca con él, se cambia el contrato, se corren sus tests y se regeneran los tipos del front (`types.ts`); no se copian a mano.
- **No duplicar lógica de estados:** usar `consolidar_control` y `calcular_estado_sistema` del contrato.
- **Ningún `CUMPLE` sin evidencia ni sin herramienta determinista.** El LLM solo propone y explica; los IDs que cite deben existir en el catálogo.
- **Auditoría:** cada evento se persiste antes de emitirse; `seq` monótono por run, asignado por un único emisor.
- **SSE:** el stream queda abierto hasta `run.finalizado` o `run.error` (con latidos); no se cierra al esperar al humano.
- **Estados finales del run:** `APROBADA`, `RECHAZADA` (plan viable rechazado), `BLOQUEADA` (plan `BLOQUEADO` rechazado, única salida) y `ERROR`.
- **Demo sin red:** `STORE_BACKEND=memory`, `LLM_MODE=fake` y modo replay deben funcionar siempre.
- **Secretos:** `.env` nunca se versiona; las claves viven solo en el backend.
- **Datos simulados** se marcan como tales en la UI; las citas normativas son reales o `simulado`.
- Textos de cara al usuario, en español.

## Estado actual

Solo hay documentación. Aún no existen `backend/`, `frontend/` ni `contract.py`; la Fase 0 (`docs/requisitos/01-fase-0-fundaciones.md`) los crea.
