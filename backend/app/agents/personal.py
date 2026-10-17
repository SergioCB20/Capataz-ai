"""Agente Personal (P3): ¿hay una persona asignada competente, vigente y libre en el turno?

Un agente delgado: las decisiones salen de `app.tools.personal` (deterministas, sin LLM). Aquí se
arma el `ResultadoRequisito` con su evidencia y se emite una traza por herramienta. Los eventos
`agente.iniciado` y `agente.completado` los emite el Supervisor (P2).
"""
from app.agents._comun import evidencia_de_asignacion, llamar_herramienta
from app.contract import (
    ACTOR_PERSONAL, AgenteSolicitud, Catalogo, Emitir, EstadoControl, Evidencia, RequisitoAVerificar,
    ResultadoRequisito, TipoRequisito, exigir_evidencia,
)
from app.tools.comun import texto_turno
from app.tools.personal import doble_asignacion, personal_disponible, verificar_certificacion


async def verificar_personal(sol: AgenteSolicitud, catalogo: Catalogo, emitir: Emitir) -> list[ResultadoRequisito]:
    turno = sol.tarea.turno
    personas = {p.id: p for p in catalogo.personas}
    disponibles = {
        p.id for p in await llamar_herramienta(
            emitir, ACTOR_PERSONAL, "personal_disponible", {"turno": texto_turno(turno)},
            lambda: personal_disponible(catalogo, turno),
            lambda r: f"{len(r)} persona(s): {', '.join(p.id for p in r) or 'ninguna'}")
    }
    dobles: dict[str, list] = {}  # persona -> otras tareas en el mismo turno (una consulta por persona)

    async def ocupaciones(persona_id: str) -> list:
        if persona_id not in dobles:
            dobles[persona_id] = await llamar_herramienta(
                emitir, ACTOR_PERSONAL, "detectar_doble_asignacion",
                {"persona": persona_id, "turno": texto_turno(turno)},
                lambda: doble_asignacion(catalogo, persona_id, sol.tarea),
                lambda r: f"{len(r)} otra(s) tarea(s)" + (f": {', '.join(t.id for t in r)}" if r else ""))
        return dobles[persona_id]

    async def verificar(pedido: RequisitoAVerificar) -> ResultadoRequisito:
        req = pedido.requisito

        def resultado(estado: EstadoControl, detalle: str, evidencia: list[Evidencia] | None = None) -> ResultadoRequisito:
            return exigir_evidencia(ResultadoRequisito(
                control_id=pedido.control_id, requisito_id=req.id, estado=estado,
                evidencia=evidencia or [], verificado_por=ACTOR_PERSONAL, detalle=detalle))

        if req.tipo != TipoRequisito.COMPETENCIA or not req.certificacion:
            return resultado(EstadoControl.NO_VERIFICABLE, "No es un requisito de competencia con certificación definida")
        codigos = [req.certificacion] + (req.certificaciones_equivalentes if sol.permitir_equivalencias else [])
        asignadas = sol.tarea.asignacion.personas
        if not asignadas:
            return resultado(EstadoControl.NO_CUMPLE, "No hay personal asignado a la tarea",
                             [evidencia_de_asignacion(sol.tarea, "asignacion.personas", [])])

        motivos: list[str] = []
        evidencia: list[Evidencia] = []
        desconocidas: list[str] = []
        for persona_id in asignadas:
            persona = personas.get(persona_id)
            if persona is None:
                desconocidas.append(persona_id)
                continue
            cert = await llamar_herramienta(
                emitir, ACTOR_PERSONAL, "verificar_certificacion",
                {"persona": persona_id, "certificaciones": codigos, "turno": texto_turno(turno)},
                lambda: verificar_certificacion(persona, codigos, turno.fecha), lambda h: h.detalle)
            if not cert.cumple:
                motivos.append(cert.detalle)
                evidencia += cert.evidencia
                continue
            if persona_id not in disponibles:
                motivos.append(f"{persona.nombre} no está disponible el turno {texto_turno(turno)}")
                evidencia.append(Evidencia(registro=f"personas/{persona_id}", campo="turnos",
                                           valor=[texto_turno(t) for t in persona.turnos], fuente=persona.fuente))
                continue
            otras = await ocupaciones(persona_id)
            if otras:
                motivos.append(f"{persona.nombre} ya está asignada a {otras[0].id} el turno {texto_turno(turno)}")
                evidencia.append(evidencia_de_asignacion(otras[0], "asignacion.personas", otras[0].asignacion.personas))
                continue
            return resultado(
                EstadoControl.CUMPLE, f"{cert.detalle}; disponible el turno {texto_turno(turno)}",
                cert.evidencia + [Evidencia(registro=f"personas/{persona_id}", campo="turnos",
                                            valor=texto_turno(turno), fuente=persona.fuente)])

        if desconocidas and not motivos:  # no se pudo evaluar a nadie: no es un incumplimiento comprobado
            return resultado(EstadoControl.NO_VERIFICABLE,
                             f"Persona(s) asignada(s) fuera del catálogo: {', '.join(desconocidas)}")
        detalle = "Ninguna persona asignada cumple: " + "; ".join(motivos)
        if desconocidas:
            detalle += f". Fuera del catálogo: {', '.join(desconocidas)}"
        return resultado(EstadoControl.NO_CUMPLE, detalle, evidencia)

    return [await verificar(pedido) for pedido in sol.requisitos]
