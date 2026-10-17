"""Evalúa cuántas fallas inyectadas detecta CAPATAZ (RF-F3-21). Datos simulados (RF-F3-22).

Uso (desde la raíz del repo):
    uv run --project backend python scripts/evaluar.py [--data-dir data] [--casos data/evaluacion.json] [--json reportes/evaluacion.json]

Ejecuta cada caso con el Supervisor, las herramientas reales y el LLM en modo fake (sin red ni claves),
imprime una tabla y guarda el reporte en JSON. Dos ejecuciones seguidas dan el mismo reporte.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from pydantic import ValidationError  # noqa: E402

from app.catalogo import CatalogoInvalido, cargar_catalogo_desde_dir  # noqa: E402
from app.contract import CasoEvaluacion  # noqa: E402
from app.evaluacion import evaluar, formatear_tabla  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=RAIZ / "data")
    parser.add_argument("--casos", type=Path, help="por defecto <data-dir>/evaluacion.json")
    parser.add_argument("--json", type=Path, default=RAIZ / "reportes" / "evaluacion.json", dest="salida")
    parser.add_argument("--sin-json", action="store_true", help="solo imprime la tabla")
    args = parser.parse_args()
    ruta = args.casos or args.data_dir / "evaluacion.json"

    logging.disable(logging.WARNING)  # los descartes del filtro de P2 no son parte del reporte
    try:
        catalogo = cargar_catalogo_desde_dir(args.data_dir)
        casos = [CasoEvaluacion.model_validate(c) for c in json.loads(ruta.read_text(encoding="utf-8"))]
    except FileNotFoundError:
        print(f"No existe {ruta}. Los casos los entrega P4 (RF-F3-20); usa --casos para indicar otro archivo.", file=sys.stderr)
        return 2
    except (CatalogoInvalido, ValidationError, json.JSONDecodeError) as e:
        print(f"Datos inválidos: {e}", file=sys.stderr)
        return 2

    reporte = asyncio.run(evaluar(catalogo, casos))
    print(formatear_tabla(reporte))
    if not args.sin_json:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(json.dumps(reporte, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nReporte JSON: {args.salida.relative_to(RAIZ) if args.salida.is_relative_to(RAIZ) else args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
