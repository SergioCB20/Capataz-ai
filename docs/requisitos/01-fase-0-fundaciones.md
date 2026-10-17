# Fase 0 — Fundaciones (0:00 – 0:40)

**Objetivo:** que cuatro personas puedan trabajar en paralelo sin bloquearse: contrato integrado, base de datos con datos semilla, backend y frontend arrancando, y un *stub* del LLM.

**Pistas paralelas sugeridas:** (A) repo + contrato + tipos TS · (B) Supabase + migración + seeds · (C) esqueleto backend + `Store` · (D) esqueleto frontend + datos de escenarios.

## Requisitos

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F0-01 | El repositorio sigue la estructura: `backend/`, `frontend/`, `data/`, `knowledge/`, `replays/`, `registry/`, `supabase/`, `docs/requisitos/`. | M | EJ | `tree -L 2` coincide; `README.md` raíz con comandos de arranque. |
| RF-F0-02 | `contract.py` y `test_contract.py` están en `backend/`; los 14 tests pasan. | M | PT | `pytest backend` en verde. |
| RF-F0-03 | Script que genera `frontend/src/api/types.ts` desde el OpenAPI de FastAPI (`openapi-typescript`). | M | EJ | Tras cambiar un modelo del contrato y re-ejecutar, cambia `types.ts`; el front compila. |
| RF-F0-04 | Proyecto Supabase creado y migración inicial aplicada (ver `90-anexo-supabase.md`). Una sola persona crea el proyecto y comparte credenciales por canal privado. | M | EJ | Las tablas existen; la migración está versionada en `supabase/migrations/`. |
| RF-F0-05 | Variables de entorno documentadas en `.env.example`: `OPENROUTER_API_KEY`, `LLM_MODEL` (por defecto, el slug de GPT-6 Luna en OpenRouter; confirmar el nombre exacto en openrouter.ai/models), `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `STORE_BACKEND` (`supabase` \| `memory`), `LLM_MODE` (`real` \| `fake`), `CORS_ORIGINS` (URL de Vercel + localhost). `.env` está en `.gitignore`. | M | EJ | Clonar + copiar `.env.example` basta para arrancar en modo `memory` + `fake`. |
| RF-F0-06 | Interfaz `Store` (repositorio) con dos implementaciones: `MemoryStore` (con volcado JSONL) y `SupabaseStore`. Operaciones: cargar catálogo, crear/leer run, agregar evento (idempotente por `(run_id, seq)`), listar eventos desde `seq`, guardar plan, guardar decisión. | M | PT | Misma suite de pruebas pasa contra ambas implementaciones. |
| RF-F0-07 | El backend arranca sin credenciales de Supabase usando `MemoryStore`, y se informa en `/api/health` (`store`, `llm_mode`). | M | EJ | Con `STORE_BACKEND=memory`, `GET /api/health` responde 200. |
| RF-F0-08 | Cargador de *seeds* **idempotente**: lee `data/*.json`, valida con `Catalogo` (Pydantic) y hace *upsert* en Supabase (o llena `MemoryStore`). Falla con mensaje claro si un JSON no valida. | M | EJ | Ejecutarlo dos veces no duplica filas; un JSON inválido aborta la carga. |
| RF-F0-09 | Datos semilla mínimos: ≥ 3 peligros, ≥ 4 tipos de tarea, ≥ 6 controles (con `bloqueante`, `aplica_a`, `fuente`), ≥ 8 personas con certificaciones y vigencias, ≥ 8 equipos con estado, ≥ 50 incidentes (RF-F0-16), y los 3 escenarios (E1, E2, E3) + E2c. Todo con `Fuente.tipo = simulado` salvo lo que cite normativa real. | M | AP | Cargar seeds termina sin errores; cada escenario referencia IDs existentes. |
| RF-F0-10 | `GET /api/catalogo` devuelve el `Catalogo` completo (peligros, tipos de tarea, controles, personal, equipos, incidentes, escenarios). | M | EJ | Respuesta valida contra `Catalogo.model_json_schema()`. |
| RF-F0-11 | Cliente LLM (OpenRouter, API compatible con OpenAI y *function calling*; modelo según `LLM_MODEL`) envuelto en un módulo propio con: tiempo límite, reintento acotado, registro de uso y **modo `fake`** que devuelve respuestas fijas por agente (para desarrollar sin créditos y para tests). Es un módulo aislado: los detalles concretos de GPT-6 Luna (parámetros, límites, formato exacto de las llamadas a funciones) **no se suponen**; se fijan al leer la documentación del evento y de OpenRouter, y el resto del sistema solo depende de la interfaz del módulo. | M | PT | Con `LLM_MODE=fake` el orquestador completa E1 sin red. |
| RF-F0-12 | Base de conocimiento normativa: `knowledge/*.md` (resúmenes con cita y marca de fuente), cargada en el contexto del Agente Riesgo. Sin vector DB. | S | AP, PT | Cada documento tiene `fuente` y referencia; ninguno inventa citas (RT-10). |
| RF-F0-13 | Esqueleto del frontend: Vite + React + TS, Tailwind + shadcn/ui, *proxy* `/api` → `:8000`, página que lista el catálogo. | M | UX | `pnpm dev` muestra escenarios desde el backend. |
| RF-F0-14 | Seguridad de base de datos: RLS activada en todas las tablas, sin políticas para `anon`; el backend usa `service_role`. | S | PT | Una consulta con la clave `anon` a `runs` devuelve 0 filas / error. |
| RF-F0-15 | CI mínimo local: `make test` (o equivalente) corre pytest y el *typecheck* del front. | C | EJ | Un comando ejecuta ambos. |
| RF-F0-16 | **Incidentes sintéticos.** `data/incidentes.json` con ≥ 50 incidentes generados con GPT-6 Luna (RF-F0-17) a partir de la **estructura** del dataset de Kaggle «Industrial Safety and Health Analytics Database» (ver nota abajo), **versionados** en el repo (no se regeneran en la demo). Modelo `Incidente` en el contrato, tabla `incidentes` en Supabase y lista en `Catalogo`. Campos mínimos: `id`, `fecha`, `planta`, `nivel_real`, `nivel_potencial`, `riesgo_critico`, `descripcion` (texto libre en español), `equipo`, `actividad`, `tipo_tarea`, `causa_raiz`, `control_fallido` (ID del catálogo), `fuente` (`tipo = simulado`). Los datos de Kaggle **no se cargan**. | M | AP, PT | Valida contra `Incidente`; cada tipo de tarea del catálogo tiene ≥ 3 incidentes relacionados. |
| RF-F0-17 | **Generador sintético** (`scripts/gen_sintetico.py`, con el LLM): produce **borradores** de personas, equipos, incidentes y tareas de evaluación. Es **reproducible** (semilla fija y temperatura baja) y guarda el resultado en `data/`. Una persona del equipo revisa la salida y la versiona en `data/*.json`; el sistema nunca la regenera al arrancar ni durante la demo. No genera citas normativas (RT-10) ni el resultado esperado de los casos de evaluación (RF-F3-20). Todo lo generado es `Fuente.tipo = simulado`. | S | AP | Los JSON generados pasan el cargador de *seeds* (RF-F0-08); el diff queda revisado en Git. |
| RF-F0-18 | **URL de la API configurable y CORS.** El frontend lee la base de la API de `VITE_API_URL` (vacía en desarrollo ⇒ usa el *proxy* `/api` → `:8000`). FastAPI permite solo los orígenes de `CORS_ORIGINS` (localhost de Vite y el dominio de Vercel). | M | EJ | El build con `VITE_API_URL=http://localhost:8000` funciona servido fuera de Vite; un origen no listado es rechazado. |
| RF-F0-19 | **Despliegue del frontend en Vercel como vitrina pública** (no se usa para presentar; ver RF-F3-45). `VITE_API_URL` apunta al backend local de la máquina del presentador. | S | EJ | La página en Vercel carga; en la máquina del presentador lista el catálogo desde el backend local **si el navegador lo permite** (verificar antes de la demo). |

### Nota: estructura del dataset de Kaggle (RF-F0-16)

Referencia: <https://www.kaggle.com/datasets/ihmstefanini/industrial-safety-and-health-analytics-database>. Solo se toma su **estructura**; sus datos no se cargan.

**Columnas: POR VERIFICAR.** Estructura probable, sin verificar: fecha, país, planta, sector, nivel de accidente, nivel de accidente potencial, género, empleado/tercero, riesgo crítico, descripción en texto libre. Probablemente no trae turno, equipo ni causa raíz; esos campos los añade el generador.

> **TODO:** dejar el CSV en `data/referencia/`, leer sus cabeceras y valores únicos (p. ej. de nivel de accidente y riesgo crítico) y ajustar el modelo `Incidente` con lo real antes de generar los datos.

## Criterios de salida de la fase

- [ ] `pytest` en verde (contrato + `Store` en ambas implementaciones).
- [ ] `GET /api/catalogo` funciona con `memory` **y** con `supabase`.
- [ ] El front muestra los escenarios del backend.
- [ ] Todo el equipo puede arrancar el proyecto desde cero siguiendo el `README`.

## Riesgos de la fase

| Riesgo | Mitigación |
|---|---|
| Configurar Supabase consume más de 15 min | Seguir con `MemoryStore`; Supabase se conecta en paralelo (RF-F0-06 lo permite). |
| Seeds incoherentes entre escenarios | Validar referencias cruzadas en el cargador (RF-F0-08). |
| Sin créditos del LLM | Modo `fake` (RF-F0-11). |
| Una página HTTPS (Vercel) que llama a `http://localhost` puede ser bloqueada por el navegador. **Verificar antes de la demo**; no se da por hecho que funcione. | La demo usa el frontend local (RF-F3-45; `pnpm dev` o `pnpm preview`). Si hace falta mostrar la URL pública conectada, abrir el backend con un túnel. |
| Datos sintéticos incoherentes o con citas inventadas | Revisión humana antes de versionar y validación del cargador (RF-F0-17). |
