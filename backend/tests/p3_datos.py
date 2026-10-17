"""Datos de prueba de P3: catálogo en `fixtures/catalogo_p3/` y casos en `fixtures/evaluacion_p3.json`."""
import json
from datetime import date
from pathlib import Path

from app.catalogo import cargar_catalogo_desde_dir
from app.contract import Asignacion, CasoEvaluacion, Catalogo, Tarea, TurnoRef

FIXTURES = Path(__file__).parent / "fixtures"
DIA = TurnoRef(fecha=date(2026, 10, 20), turno="dia")
NOCHE = TurnoRef(fecha=date(2026, 10, 20), turno="noche")


def catalogo_p3() -> Catalogo:
    return cargar_catalogo_desde_dir(FIXTURES / "catalogo_p3")


def casos_p3() -> list[CasoEvaluacion]:
    return [CasoEvaluacion.model_validate(c) for c in json.loads((FIXTURES / "evaluacion_p3.json").read_text("utf-8"))]


def tarea(personas: list[str], equipos: list[str], turno: TurnoRef = DIA, tipo: str = "TT-SOST", id_: str = "TA-X") -> Tarea:
    return Tarea(id=id_, tipo_tarea=tipo, turno=turno, asignacion=Asignacion(personas=personas, equipos=equipos))
