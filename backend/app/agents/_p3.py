"""Punto único de acceso a las piezas de P3: usa las reales si existen y los stubs si no.

Si el módulo de P3 existe pero falla al importarse, el error se propaga (no se oculta con el stub).
"""
import importlib
from typing import Any

from app.agents import _stubs

ORIGEN: dict[str, str] = {}


def _importar(modulo: str, nombre: str) -> Any:
    try:
        objeto = getattr(importlib.import_module(modulo), nombre)
        ORIGEN[nombre] = "p3"
        return objeto
    except ModuleNotFoundError as e:
        faltante = e.name or ""
        if modulo != faltante and not modulo.startswith(faltante + "."):
            raise  # falta algo que importa P3: que se vea
    ORIGEN[nombre] = "stub"
    return getattr(_stubs, nombre)


verificar_personal = _importar("app.agents.personal", "verificar_personal")
verificar_equipo = _importar("app.agents.equipo", "verificar_equipo")
buscar_incidentes = _importar("app.tools.incidentes", "buscar_incidentes")
