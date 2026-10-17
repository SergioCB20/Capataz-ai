"""Vuelca el catálogo de data/ (validado por el backend, con sus valores por defecto) a un JSON.

Se ejecuta desde backend/ con `uv run`. El frontend lo empaqueta para funcionar sin servidor
con los mismos IDs que los replays grabados (RF-F3-45/46).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())  # backend/ (cwd), no la carpeta de este script

from app.catalogo import cargar_catalogo_desde_dir  # noqa: E402

datos = Path(os.getcwd()).parent / "data"
Path(sys.argv[1]).write_text(cargar_catalogo_desde_dir(datos).model_dump_json(indent=1), encoding="utf-8")
