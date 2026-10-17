"""Seed mínimo de juguete para arrancar sin `data/` (lo reemplaza el de P4)."""

from __future__ import annotations

from datetime import date

from app.contract import (
    Asignacion,
    Catalogo,
    Certificacion,
    Control,
    Equipo,
    EstadoSistema,
    Escenario,
    Incidente,
    Peligro,
    Persona,
    Requisito,
    Tarea,
    TipoRequisito,
    TipoTarea,
    TurnoRef,
)

TURNO = TurnoRef(fecha=date(2026, 10, 17), turno="dia")


def catalogo_juguete() -> Catalogo:
    return Catalogo(
        peligros=[Peligro(id="PEL-JUG-01", nombre="Caída de rocas (juguete)")],
        tipos_tarea=[TipoTarea(id="TT-JUG-SOST", nombre="Sostenimiento con perno (juguete)")],
        controles=[
            Control(
                id="CTL-JUG-01",
                nombre="Operador con certificación de sostenimiento",
                peligro_id="PEL-JUG-01",
                aplica_a=["TT-JUG-SOST"],
                requisitos=[
                    Requisito(
                        id="REQ-JUG-01",
                        tipo=TipoRequisito.COMPETENCIA,
                        descripcion="Operador certificado en sostenimiento",
                        certificacion="CERT-SOST",
                    )
                ],
            ),
            Control(
                id="CTL-JUG-02",
                nombre="Empernador operativo y desatado previo",
                peligro_id="PEL-JUG-01",
                aplica_a=["TT-JUG-SOST"],
                requisitos=[
                    Requisito(
                        id="REQ-JUG-02",
                        tipo=TipoRequisito.EQUIPO,
                        descripcion="Empernador operativo",
                        tipo_equipo="empernador",
                    ),
                    Requisito(
                        id="REQ-JUG-03",
                        tipo=TipoRequisito.CONDICION_CAMPO,
                        descripcion="Desatado de rocas realizado",
                        pregunta_campo="¿Se realizó el desatado de rocas en la labor?",
                    ),
                ],
            ),
        ],
        personas=[
            Persona(
                id=f"PER-JUG-0{i}",
                nombre=nombre,
                rol="operador",
                certificaciones=[Certificacion(codigo="CERT-SOST", vence=vence)],
                turnos=[TURNO],
            )
            for i, (nombre, vence) in enumerate(
                [("Ana Quispe", date(2027, 3, 1)), ("Luis Huamán", date(2026, 9, 30)), ("Rosa Mamani", date(2027, 1, 15))],
                start=1,
            )
        ],
        equipos=[
            Equipo(id="EQ-JUG-01", nombre="Empernador 01", tipo_equipo="empernador"),
            Equipo(id="EQ-JUG-02", nombre="Empernador 02", tipo_equipo="empernador", estado="mantenimiento"),
        ],
        incidentes=[
            Incidente(
                id="INC-JUG-01",
                fecha=date(2025, 5, 4),
                nivel_potencial="IV",
                riesgo_critico="caída de rocas",
                descripcion="Desprendimiento de roca durante el sostenimiento (simulado).",
                equipo="empernador",
                actividad="sostenimiento",
                tipo_tarea="TT-JUG-SOST",
                control_fallido="CTL-JUG-02",
            )
        ],
        escenarios=[
            Escenario(
                id="E1",
                nombre="Caso limpio (juguete)",
                tarea=Tarea(
                    id="TAR-JUG-E1",
                    tipo_tarea="TT-JUG-SOST",
                    descripcion="Sostenimiento con pernos en la labor 3 (juguete)",
                    zona="Nivel 3",
                    turno=TURNO,
                    asignacion=Asignacion(personas=["PER-JUG-01"], equipos=["EQ-JUG-01"]),
                ),
                resultado_esperado=EstadoSistema.RECOMENDADO,
            )
        ],
    )
