# Checklist previo a la demo (RF-F3-41)

Marcar cada punto antes de subir al escenario. Lo que no se pueda marcar, pasar al [plan B](plan-b.md).

## Máquina del presentador (todo local, sin depender de Internet)

- [ ] **Backend** arriba en `:8000`:
  `cd backend && STORE_BACKEND=memory LLM_MODE=fake uv run uvicorn app.main:app --port 8000`
- [ ] `GET http://localhost:8000/api/health` responde `{"store":"memory","llm_mode":"fake","orquestador":"p2"}`.
- [ ] `GET http://localhost:8000/api/catalogo` lista los escenarios **E1, E2, E2c y E3** (si solo sale E1, el backend está usando el catálogo de juguete: falta la carpeta `data/`).
- [ ] **Frontend local** construido y servido: `cd frontend && VITE_API_URL=http://localhost:8000 pnpm build && pnpm preview` → <http://localhost:4173>.
- [ ] **CORS** probado: abrir el frontend en `localhost:4173` y evaluar E1 en modo «En vivo». El backend permite `localhost:5173` y `localhost:4173` por defecto (`CORS_ORIGINS`).
- [ ] Recorrer **E1, E2 y E3** una vez en modo «En vivo» y otra en modo «Replay (corrida grabada, sin red)».
- [ ] **Replays presentes** en `replays/`: hoy solo existe `e1.json` (escrito a mano). Faltan los de E2, E2c y E3 grabados de corridas reales: ver «Grabar los replays».
- [ ] `.env` legible: todas las líneas con formato `CLAVE=valor`. (Una línea mal formada se ignora en silencio y no carga la variable.)
- [ ] `LLM_MODE` decidido: **`fake`** para la demo (rápido, reproducible, sin créditos). Con `real` hay que tener `OPENROUTER_API_KEY` y `LLM_MODEL` y haber probado el modelo antes.
- [ ] Navegador en pantalla completa, zoom fijado, notificaciones silenciadas, otras pestañas cerradas.
- [ ] Guion en mano y cronómetro; ensayado ≥ 2 veces.

## Solo si se usa Supabase (opcional; la demo funciona sin él)

- [ ] El proyecto no está **pausado** (el plan gratuito se pausa tras 7 días sin actividad): hacer una consulta antes.
- [ ] `STORE_BACKEND=supabase` con `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` válidos, y los seeds cargados: `uv run --project backend python scripts/cargar_seeds.py`.
- [ ] La migración `supabase/migrations/0001_init.sql` está aplicada (tablas con RLS).
- [ ] Si algo falla, **no improvisar**: volver a `STORE_BACKEND=memory`.

## Grabar los replays (pendiente)

Con el backend en `fake` y una corrida de cada escenario terminada, para cada una: `uv run --project backend python scripts/grabar_replay.py <run_id> <E1|E2|E2c|E3>`. El `run_id` sale de `POST /api/runs` (campo `run_id`). Revisar el resultado antes de reemplazar `replays/e1.json`, que es de P5.

## Vitrina en Vercel (no se usa para presentar)

Una página HTTPS que llama a `http://localhost` puede ser bloqueada por el navegador. Verificarlo antes si se quiere mostrar la URL pública; la demo se hace con el frontend local.
