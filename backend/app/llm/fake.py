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
    """Peligros del tipo de tarea, sus controles aplicables e incidentes de `buscar_incidentes`."""
    catalogo = ctx.contexto["catalogo"]
    tarea = ctx.contexto["tarea"]
    tipo = next(t for t in catalogo.tipos_tarea if t.id == tarea.tipo_tarea)
    peligros = []
    for peligro_id in tipo.peligros:
        peligro = next((p for p in catalogo.peligros if p.id == peligro_id), None)
        if peligro is None:
            continue
        controles = [c.id for c in catalogo.controles
                     if c.peligro_id == peligro_id and tarea.tipo_tarea in c.aplica_a]
        encontrados = json.loads(await ctx.llamar(
            "buscar_incidentes", actividad=tipo.nombre, riesgo_critico=peligro.categoria))
        peligros.append({
            "peligro_id": peligro_id,
            "justificacion": f"{peligro.nombre}: peligro asociado al tipo de tarea «{tipo.nombre}».",
            "controles": controles,
            "incidentes_similares": [i["id"] for i in encontrados[:2]],
        })
    return {"peligros": peligros}


registrar_fake("riesgo", _riesgo_por_defecto)
