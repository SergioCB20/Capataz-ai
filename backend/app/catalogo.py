"""Carga del catálogo desde `data/<campo>.json` (un arreglo por campo de `Catalogo`).

Archivos esperados (los escribe P4): `peligros.json`, `tipos_tarea.json`,
`controles.json`, `personas.json`, `equipos.json`, `incidentes.json`,
`escenarios.json`. Si no hay ninguno, se usa el seed de juguete.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.contract import Catalogo

log = logging.getLogger(__name__)


class CatalogoInvalido(Exception):
    pass


def cargar_catalogo_desde_dir(data_dir: Path | None) -> Catalogo:
    datos: dict[str, list] = {}
    if data_dir is not None and data_dir.is_dir():
        for campo in Catalogo.model_fields:
            ruta = data_dir / f"{campo}.json"
            if ruta.exists():
                try:
                    datos[campo] = json.loads(ruta.read_text(encoding="utf-8"))
                except json.JSONDecodeError as e:
                    raise CatalogoInvalido(f"{ruta.name}: JSON inválido ({e})") from e

    if not datos:
        from app.seed_juguete import catalogo_juguete

        log.warning("Sin archivos en %s: se usa el seed de juguete", data_dir)
        return catalogo_juguete()

    try:
        catalogo = Catalogo.model_validate(datos)
    except ValidationError as e:
        raise CatalogoInvalido(f"Catálogo en {data_dir} no valida contra el contrato:\n{e}") from e
    _validar_referencias(catalogo)
    return catalogo


def _validar_referencias(c: Catalogo) -> None:
    """Referencias cruzadas mínimas (RF-F0-08)."""
    tipos = {t.id for t in c.tipos_tarea}
    peligros = {p.id for p in c.peligros}
    personas = {p.id for p in c.personas}
    equipos = {e.id for e in c.equipos}
    errores: list[str] = []
    for ctrl in c.controles:
        if peligros and ctrl.peligro_id not in peligros:
            errores.append(f"control {ctrl.id}: peligro {ctrl.peligro_id} no existe")
        errores += [f"control {ctrl.id}: tipo {t} no existe" for t in ctrl.aplica_a if tipos and t not in tipos]
    for esc in c.escenarios:
        t = esc.tarea
        if tipos and t.tipo_tarea not in tipos:
            errores.append(f"escenario {esc.id}: tipo de tarea {t.tipo_tarea} no existe")
        errores += [f"escenario {esc.id}: persona {p} no existe" for p in t.asignacion.personas if p not in personas]
        errores += [f"escenario {esc.id}: equipo {e} no existe" for e in t.asignacion.equipos if e not in equipos]
    if errores:
        raise CatalogoInvalido("Referencias rotas en el catálogo:\n- " + "\n- ".join(errores))
