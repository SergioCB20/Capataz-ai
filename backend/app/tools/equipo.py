"""Herramientas deterministas de Equipo (RF-F1-14): tipo requerido, estado y disponibilidad en el turno.

Reglas sobre los datos del catálogo:
- Un equipo cubre un tipo si `tipo_equipo` coincide. Solo con `permitir_equivalencias` (alternativas)
  también lo cubre si el tipo requerido está en `Equipo.tipos_equivalentes`.
- Es utilizable si `estado` es `operativo` y el turno no figura en `Equipo.mantenimiento`.
"""
from app.contract import Equipo, EstadoEquipo, Evidencia, TurnoRef
from app.tools.comun import Hallazgo, texto_turno


def cubre_tipo(equipo: Equipo, tipo_requerido: str, permitir_equivalencias: bool) -> Hallazgo:
    evidencia = [Evidencia(registro=f"equipos/{equipo.id}", campo="tipo_equipo", valor=equipo.tipo_equipo,
                           fuente=equipo.fuente)]
    if equipo.tipo_equipo == tipo_requerido:
        return Hallazgo(True, f"{equipo.nombre} es del tipo {tipo_requerido}", evidencia)
    if permitir_equivalencias and tipo_requerido in equipo.tipos_equivalentes:
        return Hallazgo(True, f"{equipo.nombre} ({equipo.tipo_equipo}) es equivalente a {tipo_requerido}", evidencia)
    return Hallazgo(False, f"{equipo.nombre} es del tipo {equipo.tipo_equipo}, no {tipo_requerido}", evidencia)


def estado_equipo(equipo: Equipo, turno: TurnoRef) -> Hallazgo:
    registro = f"equipos/{equipo.id}"
    if equipo.estado != EstadoEquipo.OPERATIVO:
        estado = {EstadoEquipo.MANTENIMIENTO: "mantenimiento", EstadoEquipo.FUERA_SERVICIO: "fuera de servicio"}[equipo.estado]
        return Hallazgo(False, f"{equipo.nombre} está en {estado}",
                        [Evidencia(registro=registro, campo="estado", valor=equipo.estado.value, fuente=equipo.fuente)])
    if turno in equipo.mantenimiento:
        return Hallazgo(False, f"{equipo.nombre} tiene mantenimiento programado el turno {texto_turno(turno)}",
                        [Evidencia(registro=registro, campo="mantenimiento",
                                   valor=[texto_turno(t) for t in equipo.mantenimiento], fuente=equipo.fuente)])
    return Hallazgo(True, f"{equipo.nombre} operativo y disponible el turno {texto_turno(turno)}",
                    [Evidencia(registro=registro, campo="estado", valor=equipo.estado.value, fuente=equipo.fuente)])
