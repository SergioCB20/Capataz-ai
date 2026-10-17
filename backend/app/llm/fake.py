"""Modo fake: respuestas fijas por agente y escenario, sin red.

Una respuesta fake es una función `(ContextoFake) -> dict | BaseModel` (sync o async).
Se busca primero por (agente, escenario_id) y, si no hay, por (agente, None).
Las respuestas se derivan del catálogo recibido en el contexto, no de IDs fijos,
para no depender de los seeds concretos de P4.
"""
import json
from typing import Any, Callable

from app.llm.tipos import ContextoFake

FakeFn = Callable[[ContextoFake], Any]

_REGISTRO: dict[tuple[str, str | None], FakeFn] = {}


def registrar_fake(agente: str, fn: FakeFn, escenario_id: str | None = None) -> None:
    _REGISTRO[(agente, escenario_id)] = fn


def buscar_fake(agente: str, escenario_id: str | None) -> FakeFn | None:
    return _REGISTRO.get((agente, escenario_id)) or _REGISTRO.get((agente, None))


async def _riesgo_por_defecto(ctx: ContextoFake) -> dict[str, Any]:
    """Peligros de los controles que aplican al tipo de tarea, e incidentes de `buscar_incidentes`."""
    catalogo = ctx.contexto["catalogo"]
    tarea = ctx.contexto["tarea"]
    tipo = next((t for t in catalogo.tipos_tarea if t.id == tarea.tipo_tarea), None)
    actividad = tipo.nombre if tipo else tarea.tipo_tarea
    controles_por_peligro: dict[str, list[str]] = {}
    for control in catalogo.controles:
        if tarea.tipo_tarea in control.aplica_a:
            controles_por_peligro.setdefault(control.peligro_id, []).append(control.id)

    peligros = []
    for peligro_id, controles in controles_por_peligro.items():
        peligro = next((p for p in catalogo.peligros if p.id == peligro_id), None)
        if peligro is None:
            continue
        encontrados = json.loads(await ctx.llamar(
            "buscar_incidentes", actividad=actividad, riesgo_critico=peligro.nombre))
        peligros.append({
            "peligro_id": peligro_id,
            "justificacion": f"{peligro.nombre}: peligro asociado a «{actividad}».",
            "controles": controles,
            "incidentes_similares": [i["id"] for i in encontrados[:2]],
        })
    return {"peligros": peligros}


registrar_fake("riesgo", _riesgo_por_defecto)
