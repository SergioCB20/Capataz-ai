# CAPATAZ — frontend (P5)

Vite 6 + React 19 + TypeScript + Tailwind 4 + shadcn/ui + React Flow. Toda la UI se deriva de un único reductor de eventos (`src/eventos/reductor.ts`), igual en vivo (SSE) y en replay.

## Arranque

```bash
pnpm install
pnpm dev        # http://localhost:5173 ; proxy /api -> http://localhost:8000
pnpm test       # vitest
pnpm build      # tsc + build a dist/
pnpm preview    # sirve dist/ en http://localhost:4173 (también con proxy /api)
```

Node ≥ 20.18 (Vite 6). `VITE_API_URL` (ver `.env.example`): vacío = mismo origen + proxy; si no, la URL del backend. No lleva secretos.

## Modos

| Situación | Qué pasa |
|---|---|
| Backend arriba, modo **en vivo** | `POST /api/runs` + SSE `/api/runs/{id}/eventos` (reconexión con `Last-Event-ID` / `?desde=`). |
| Backend arriba, modo **replay** | El backend reproduce `replays/<escenario>.json`; si no lo tiene, se usa el replay local. |
| **Sin backend** | Catálogo de demostración (`src/datos/catalogoDemo.ts`) y replay local en el navegador. La decisión se simula y no se guarda. |

Replays locales: primero `../replays/*.json` (grabados por P1 desde corridas reales) y, si falta alguno, los fixtures provisionales escritos a mano en `src/__fixtures__/` (E2, E2c, E3). Todos se empaquetan en el build, así que la demo **no necesita Internet** (RF-F3-45).

## Demo sin Wi-Fi (RF-F3-45)

```bash
pnpm build && pnpm preview   # abrir http://localhost:4173 y elegir «Replay»
```

Comprobado: el build solo pide recursos a `localhost` (las fuentes van empaquetadas).

## Vitrina en Vercel (RF-F0-19, RF-F3-46)

1. En Vercel: **New Project** → importar el repo → **Root Directory = `frontend`**. `vercel.json` ya fija Vite, `pnpm build` y `dist/`.
2. El proyecto usa **pnpm 12** (`packageManager` en `package.json`). Si el build de Vercel falla por la versión de pnpm, añadir la variable `ENABLE_EXPERIMENTAL_COREPACK=1`.
3. Variable opcional `VITE_API_URL` (p. ej. `http://localhost:8000`). Sin ella, la vitrina funciona sola con los replays locales.
4. **Verificar antes de la demo:** una página HTTPS (Vercel) que llama a `http://localhost` puede ser bloqueada por el navegador. La demo se presenta con el frontend **local**; Vercel es solo vitrina.
5. En el backend, `CORS_ORIGINS` debe incluir la URL de Vercel si se quiere conectar.
