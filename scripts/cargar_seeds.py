"""Carga `data/*.json` en Supabase (RF-F0-08). Idempotente: se puede ejecutar las veces que haga falta.

Uso (desde la raíz del repo):
    uv run --project backend python scripts/cargar_seeds.py --dry-run   # solo valida, no toca Supabase
    uv run --project backend python scripts/cargar_seeds.py             # valida y hace upsert

Valida los 7 archivos del catálogo contra el contrato (con sus referencias cruzadas) y, si existe,
`evaluacion.json`. Si algo no valida, aborta sin cargar nada. Usa SUPABASE_URL y
SUPABASE_SERVICE_ROLE_KEY del entorno o del `.env`; la clave solo la usa este script en tu máquina.
El upsert actualiza por `id` y no borra filas que ya no estén en los JSON.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from pydantic import ValidationError  # noqa: E402

from app.catalogo import CatalogoInvalido, cargar_catalogo_desde_dir  # noqa: E402
from app.config import Settings  # noqa: E402  (también carga el .env)
from app.contract import CasoEvaluacion, Catalogo  # noqa: E402
from app.store.supabase_store import filas_catalogo  # noqa: E402


def validar(data_dir: Path) -> Catalogo:
    faltan = [c for c in Catalogo.model_fields if not (data_dir / f"{c}.json").exists()]
    if faltan:
        raise CatalogoInvalido(f"Faltan archivos en {data_dir}: {', '.join(f + '.json' for f in faltan)}")
    catalogo = cargar_catalogo_desde_dir(data_dir)  # valida contrato y referencias cruzadas
    ruta = data_dir / "evaluacion.json"
    if ruta.exists():
        for caso in json.loads(ruta.read_text(encoding="utf-8")):
            CasoEvaluacion.model_validate(caso)
    return catalogo


async def cargar(catalogo: Catalogo) -> dict[str, int]:
    from supabase import acreate_client

    url, clave = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not clave:
        raise RuntimeError("Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY (entorno o .env)")
    db = await acreate_client(url, clave)
    cuentas = {}
    for tabla, filas in filas_catalogo(catalogo).items():
        if filas:
            await db.table(tabla).upsert(filas, on_conflict="id").execute()
        cuentas[tabla] = len(filas)
    return cuentas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=Settings().data_dir)
    parser.add_argument("--dry-run", action="store_true", help="solo valida los JSON")
    args = parser.parse_args()

    try:
        catalogo = validar(args.data_dir)
    except (CatalogoInvalido, ValidationError, json.JSONDecodeError) as e:
        print(f"Los datos no validan; no se cargó nada.\n{e}", file=sys.stderr)
        return 2
    cuentas = {t: len(f) for t, f in filas_catalogo(catalogo).items()}
    print("Datos válidos: " + ", ".join(f"{n} {t}" for t, n in cuentas.items()))
    if args.dry_run:
        return 0
    try:
        asyncio.run(cargar(catalogo))
    except Exception as e:
        print(f"No se pudo cargar en Supabase: {type(e).__name__}: {e}", file=sys.stderr)
        return 3
    print("Cargado en Supabase (upsert por id).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
