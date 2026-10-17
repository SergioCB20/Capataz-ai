"""Piezas comunes de las herramientas deterministas de verificación (P3). Sin LLM ni eventos."""
from dataclasses import dataclass, field
from datetime import date

from app.contract import Evidencia, TurnoRef


@dataclass
class Hallazgo:
    """Resultado de una herramienta: si se cumple, por qué, y qué registro lo respalda."""
    cumple: bool
    detalle: str
    evidencia: list[Evidencia] = field(default_factory=list)


def texto_fecha(fecha: date) -> str:
    return fecha.strftime("%d/%m/%Y")


def texto_turno(turno: TurnoRef) -> str:
    return f"{texto_fecha(turno.fecha)} {'día' if turno.turno == 'dia' else 'noche'}"
