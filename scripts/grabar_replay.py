"""Graba los eventos de un run como replay (RF-F3-01).

Uso (con el backend corriendo):
    uv run --project backend python scripts/grabar_replay.py <run_id> <escenario_id> [--api http://localhost:8000]

Escribe `replays/<escenario_id>.json` y valida cada evento contra el contrato.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from app.contract import Evento, validar_payload  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_id")
    parser.add_argument("escenario_id")
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()

    url = f"{args.api.rstrip('/')}/api/runs/{args.run_id}/auditoria"
    with urllib.request.urlopen(url) as resp:
        datos = json.load(resp)

    eventos = [Evento.model_validate(d) for d in datos]
    for ev in eventos:
        validar_payload(ev)
    if not eventos:
        print("El run no tiene eventos", file=sys.stderr)
        return 1

    destino = RAIZ / "replays" / f"{args.escenario_id}.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(
        json.dumps([json.loads(e.model_dump_json()) for e in eventos], ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"{len(eventos)} eventos -> {destino.relative_to(RAIZ)} (ultimo: {eventos[-1].tipo})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
