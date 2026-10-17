## Why

Sin datos coherentes los escenarios no demuestran nada: E2 necesita un equipo en mantenimiento con alternativa, E3 necesita que no haya ninguna. P4 es dueño de los datos simulados, la base de conocimiento normativa, la persistencia en Supabase y el guion de la demo.

## What Changes

- Seeds en `data/*.json`: peligros, tipos de tarea, controles, personas, equipos y los escenarios E1, E2, E2c y E3.
- Al menos 50 incidentes sintéticos con la estructura del dataset de Kaggle y generador reproducible.
- Conjunto de evaluación con al menos 15 casos y resultado esperado fijado por el equipo.
- `knowledge/*.md`: un resumen por PDF oficial, con citas verificadas.
- Migración SQL, proyecto Supabase con RLS, `SupabaseStore` y cargador de seeds idempotente.
- Guion de demo, checklist previo, plan B y material para la rúbrica.

## Capabilities

### New Capabilities
- `datos-semilla`: catálogo y escenarios simulados coherentes con los resultados esperados.
- `incidentes-sinteticos`: incidentes generados, revisados y versionados.
- `base-conocimiento`: resúmenes normativos con citas verificadas.
- `persistencia-supabase`: esquema, RLS, `SupabaseStore` y cargador de seeds.
- `preparacion-demo`: guion, checklist, plan B y material de rúbrica.

### Modified Capabilities
<!-- Ninguna. -->

## Impact

- Archivos: `data/`, `knowledge/`, `supabase/migrations/`, `backend/app/store/supabase_store.py`, `scripts/gen_sintetico.py`, `scripts/cargar_seeds.py`, `docs/demo/`.
- Lo consumen P1 (catálogo y escenarios), P3 (evaluación y pruebas) y P5 (presets).
- Requisitos: RF-F0-04, 08, 09, 12, 14, 16, 17 · RF-F3-20, 22, 40–44 · RT-07, RT-10.
