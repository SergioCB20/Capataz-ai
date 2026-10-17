"""Herramientas deterministas de Personal (RF-F1-13): disponibilidad, vigencia y doble asignación.

Reglas sobre los datos del catálogo:
- Disponible en un turno = el turno está en `Persona.turnos`.
- Una certificación es vigente si `vence` >= fecha del turno (inclusive).
- Doble asignación = otra tarea del catálogo (`Catalogo.escenarios`, distinta id) en el mismo turno
  con la misma persona asignada.
"""
from datetime import date

from app.contract import Catalogo, Evidencia, Persona, Tarea, TurnoRef
from app.tools.comun import Hallazgo, texto_fecha


def personal_disponible(catalogo: Catalogo, turno: TurnoRef) -> list[Persona]:
    return [p for p in catalogo.personas if turno in p.turnos]


def verificar_certificacion(persona: Persona, codigos: list[str], fecha: date) -> Hallazgo:
    """¿Tiene alguna de las certificaciones `codigos` vigente a `fecha`? Se evalúa la de mayor vencimiento."""
    registro = f"personas/{persona.id}"
    coinciden = [c for c in persona.certificaciones if c.codigo in codigos]
    if not coinciden:
        tiene = [c.codigo for c in persona.certificaciones]
        return Hallazgo(
            False,
            f"{persona.nombre} no tiene {' ni '.join(codigos)} (tiene: {', '.join(tiene) or 'ninguna'})",
            [Evidencia(registro=registro, campo="certificaciones", valor=tiene, fuente=persona.fuente)],
        )
    mejor = max(coinciden, key=lambda c: c.vence)
    evidencia = [Evidencia(registro=registro, campo=f"certificaciones.{mejor.codigo}.vence",
                           valor=mejor.vence.isoformat(), fuente=persona.fuente)]
    if mejor.vence >= fecha:
        return Hallazgo(True, f"{persona.nombre}: {mejor.codigo} vigente hasta el {texto_fecha(mejor.vence)}", evidencia)
    return Hallazgo(
        False,
        f"{persona.nombre}: {mejor.codigo} venció el {texto_fecha(mejor.vence)} (turno del {texto_fecha(fecha)})",
        evidencia,
    )


def doble_asignacion(catalogo: Catalogo, persona_id: str, tarea: Tarea) -> list[Tarea]:
    """Otras tareas del catálogo, en el mismo turno, que ya tienen asignada a la persona."""
    return [e.tarea for e in catalogo.escenarios
            if e.tarea.id != tarea.id and e.tarea.turno == tarea.turno and persona_id in e.tarea.asignacion.personas]
