"""STUBS de P3 con la firma acordada. Se reemplazan por los reales con un cambio de import.

Devuelven `NO_VERIFICABLE` o listas vacías: nunca `CUMPLE` (RF-F1-06).
"""
from app.agents._contrato import (
    AgenteSolicitud, Catalogo, Emitir, EstadoControl, Incidente, ResultadoRequisito, TipoRequisito,
)


def _no_verificable(sol: AgenteSolicitud, tipo: TipoRequisito, agente_id: str) -> list[ResultadoRequisito]:
    return [
        ResultadoRequisito(
            control_id=r.control_id,
            requisito_id=r.requisito.id,
            estado=EstadoControl.NO_VERIFICABLE,
            verificado_por=agente_id,
            detalle="Stub de P3: verificación pendiente de implementar.",
        )
        for r in sol.requisitos
        if r.requisito.tipo == tipo
    ]


async def verificar_personal(sol: AgenteSolicitud, catalogo: Catalogo, emitir: Emitir) -> list[ResultadoRequisito]:
    return _no_verificable(sol, TipoRequisito.COMPETENCIA, "capataz:agente-personal")


async def verificar_equipo(sol: AgenteSolicitud, catalogo: Catalogo, emitir: Emitir) -> list[ResultadoRequisito]:
    return _no_verificable(sol, TipoRequisito.EQUIPO, "capataz:agente-equipo")


def buscar_incidentes(
    catalogo: Catalogo,
    equipo: str | None = None,
    actividad: str | None = None,
    riesgo_critico: str | None = None,
    limite: int = 5,
) -> list[Incidente]:
    return []
