"""Vuelca el OpenAPI de la app FastAPI a un archivo JSON. Se ejecuta desde backend/ con `uv run`."""

import json
import os
import sys

sys.path.insert(0, os.getcwd())  # backend/ (cwd), no la carpeta de este script

from app.main import app  # noqa: E402

with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(app.openapi(), f, ensure_ascii=False, indent=2)
