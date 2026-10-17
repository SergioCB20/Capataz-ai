"""Carga `data/*.json` en Supabase de forma idempotente (RF-F0-08).

Uso: uv run --project backend python scripts/cargar_seeds.py

Valida el catálogo contra el contrato (y sus referencias cruzadas) antes de subir
nada; un JSON inválido aborta la carga. Reejecutarlo no duplica filas (upsert).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from app.catalogo import CatalogoInvalido, cargar_catalogo_desde_dir  # noqa: E402
from app.config import Settings  # noqa: E402
from app.store.supabase_store import SupabaseStore  # noqa: E402


async def main() -> int:
    settings = Settings()
    try:
        c = cargar_catalogo_desde_dir(settings.data_dir)
    except CatalogoInvalido as e:
        print(f"Catálogo inválido, no se sube nada:\n{e}", file=sys.stderr)
        return 1

    store = SupabaseStore.desde_entorno()
    j = lambda m: m.model_dump(mode="json")  # noqa: E731
    filas = {
        "peligros": [{"id": x.id, "data": j(x)} for x in c.peligros],
        "tipos_tarea": [{"id": x.id, "data": j(x)} for x in c.tipos_tarea],
        "controles": [{"id": x.id, "peligro_id": x.peligro_id, "bloqueante": x.bloqueante, "data": j(x)} for x in c.controles],
        "personas": [{"id": x.id, "data": j(x)} for x in c.personas],
        "equipos": [{"id": x.id, "tipo_equipo": x.tipo_equipo, "data": j(x)} for x in c.equipos],
        "incidentes": [{"id": x.id, "tipo_tarea_id": x.tipo_tarea, "data": j(x)} for x in c.incidentes],
        "escenarios": [{"id": x.id, "data": j(x)} for x in c.escenarios],
    }
    for tabla, datos in filas.items():
        await store.upsert(tabla, datos)
        print(f"{tabla}: {len(datos)} filas")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
