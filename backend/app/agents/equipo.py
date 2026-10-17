"""Agente Equipo (P3): ¿hay un equipo asignado del tipo requerido, operativo y libre en el turno?

Un agente delgado: las decisiones salen de `app.tools.equipo` (deterministas, sin LLM). Los tipos
equivalentes solo cuentan con `permitir_equivalencias` (RT-06). Los eventos `agente.iniciado` y
`agente.completado` los emite el Supervisor (P2).
"""
from app.agents._comun import evidencia_de_asignacion, llamar_herramienta
from app.contract import (
    ACTOR_EQUIPO, AgenteSolicitud, Catalogo, Emitir, EstadoControl, Evidencia, RequisitoAVerificar,
    ResultadoRequisito, TipoRequisito, exigir_evidencia,
)
from app.tools.comun import texto_turno
from app.tools.equipo import cubre_tipo, estado_equipo


async def verificar_equipo(sol: AgenteSolicitud, catalogo: Catalogo, emitir: Emitir) -> list[ResultadoRequisito]:
    turno = sol.tarea.turno
    equipos = {e.id: e for e in catalogo.equipos}

    async def verificar(pedido: RequisitoAVerificar) -> ResultadoRequisito:
        req = pedido.requisito

        def resultado(estado: EstadoControl, detalle: str, evidencia: list[Evidencia] | None = None) -> ResultadoRequisito:
            return exigir_evidencia(ResultadoRequisito(
                control_id=pedido.control_id, requisito_id=req.id, estado=estado,
                evidencia=evidencia or [], verificado_por=ACTOR_EQUIPO, detalle=detalle))

        if req.tipo != TipoRequisito.EQUIPO or not req.tipo_equipo:
            return resultado(EstadoControl.NO_VERIFICABLE, "No es un requisito de equipo con tipo definido")
        asignados = sol.tarea.asignacion.equipos
        if not asignados:
            return resultado(EstadoControl.NO_CUMPLE, "No hay equipo asignado a la tarea",
                             [evidencia_de_asignacion(sol.tarea, "asignacion.equipos", [])])

        sin_tipo: list[str] = []      # asignados que no son del tipo pedido
        inutilizables: list[str] = []  # del tipo pedido, pero en mantenimiento o fuera de servicio
        evidencia: list[Evidencia] = []
        desconocidos: list[str] = []
        for equipo_id in asignados:
            equipo = equipos.get(equipo_id)
            if equipo is None:
                desconocidos.append(equipo_id)
                continue
            tipo = await llamar_herramienta(
                emitir, ACTOR_EQUIPO, "verificar_tipo_equipo",
                {"equipo": equipo_id, "tipo_requerido": req.tipo_equipo, "equivalencias": sol.permitir_equivalencias},
                lambda: cubre_tipo(equipo, req.tipo_equipo, sol.permitir_equivalencias), lambda h: h.detalle)
            if not tipo.cumple:
                sin_tipo.append(tipo.detalle)
                continue
            estado = await llamar_herramienta(
                emitir, ACTOR_EQUIPO, "consultar_estado_equipo",
                {"equipo": equipo_id, "turno": texto_turno(turno)},
                lambda: estado_equipo(equipo, turno), lambda h: h.detalle)
            if estado.cumple:
                return resultado(EstadoControl.CUMPLE, f"{tipo.detalle}; {estado.detalle}",
                                 tipo.evidencia + estado.evidencia)
            inutilizables.append(estado.detalle)
            evidencia += estado.evidencia

        if desconocidos and not inutilizables and not sin_tipo:
            return resultado(EstadoControl.NO_VERIFICABLE,
                             f"Equipo(s) asignado(s) fuera del catálogo: {', '.join(desconocidos)}")
        if inutilizables:  # lo más útil de decir: había un equipo del tipo, pero no se puede usar
            return resultado(EstadoControl.NO_CUMPLE, "Ningún equipo asignado está disponible: " + "; ".join(inutilizables),
                             evidencia)
        return resultado(
            EstadoControl.NO_CUMPLE,
            f"Ningún equipo asignado es del tipo {req.tipo_equipo}: " + "; ".join(sin_tipo or ["ninguno válido"]),
            [evidencia_de_asignacion(sol.tarea, "asignacion.equipos", asignados)])

    return [await verificar(pedido) for pedido in sol.requisitos]
