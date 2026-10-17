"""Agente Riesgo (P2): peligros, controles del catálogo e incidentes similares.

El LLM razona y justifica; el código filtra y completa. Todo ID que cite el LLM se valida
contra el catálogo (RF-F1-10) y los incidentes solo valen si `buscar_incidentes` los devolvió
en esta evaluación (RF-F1-19). Además, todo control del catálogo que aplica al tipo de tarea
queda siempre exigido: que el LLM omita uno no puede dejarlo sin verificar (RT-01).
"""
import inspect
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable

from app.agents import _stubs
from app.agents._contrato import (
    ACTOR_RIESGO, Catalogo, Emitir, EvaluacionRiesgo, Incidente, PeligroDetectado, Tarea, TipoEvento,
    TraceHerramienta,
)
from app.llm import ClienteLLM, Herramienta, LLMError, get_cliente

log = logging.getLogger("capataz.riesgo")

ACTOR = ACTOR_RIESGO
NOMBRE_LLM = "riesgo"
MAX_CONOCIMIENTO = 12_000
LIMITE_INCIDENTES = 5

SISTEMA = """Eres el Agente Riesgo de CAPATAZ, un sistema que verifica, antes de una tarea minera, \
que sus controles críticos pueden ejecutarse. Tu trabajo es identificar los peligros de la tarea y \
los controles del catálogo que aplican. No decides si algo se cumple: eso lo verifica el código.

Reglas:
- Usa SOLO los IDs de peligro y de control de la lista que se te entrega. No inventes IDs.
- Antes de concluir, consulta `buscar_incidentes` para cada peligro relevante. Cita en \
`incidentes_similares` únicamente IDs que esa herramienta haya devuelto.
- Un incidente puede justificar sumar un control del catálogo que no aplica al tipo de tarea, \
solo si es el `control_fallido` de ese incidente.
- `justificacion`: máximo 2 frases, basada en la tarea, los incidentes y la base de conocimiento. \
Si no tienes respaldo para una afirmación, no la hagas.
- Termina siempre llamando a la función `responder`."""

PARAMETROS_BUSCAR = {
    "type": "object",
    "properties": {
        "equipo": {"type": "string", "description": "Equipo involucrado, si se conoce"},
        "actividad": {"type": "string", "description": "Actividad o tipo de tarea"},
        "riesgo_critico": {"type": "string", "description": "Riesgo crítico o categoría de peligro"},
    },
}


def cargar_conocimiento(directorio: Path | None = None, max_chars: int = MAX_CONOCIMIENTO) -> str:
    """Resúmenes normativos de `knowledge/*.md` para el contexto del LLM (sin vector DB)."""
    if directorio is None:
        directorio = Path(os.getenv("KNOWLEDGE_DIR") or Path(__file__).resolve().parents[3] / "knowledge")
    if not directorio.is_dir():
        return ""
    partes = [f"### {p.name}\n{p.read_text(encoding='utf-8')}" for p in sorted(directorio.glob("*.md"))]
    return "\n\n".join(partes)[:max_chars]


def controles_exigidos(evaluacion: EvaluacionRiesgo) -> list[str]:
    """IDs de control únicos, en el orden en que aparecen."""
    vistos: dict[str, None] = {}
    for peligro in evaluacion.peligros:
        vistos.update(dict.fromkeys(peligro.controles))
    return list(vistos)


def filtrar_y_completar(
    bruto: EvaluacionRiesgo | None,
    tarea: Tarea,
    catalogo: Catalogo,
    incidentes_vistos: set[str],
) -> tuple[EvaluacionRiesgo, list[str]]:
    """Deja solo IDs del catálogo y suma los controles base. Devuelve (evaluación, descartes)."""
    descartes: list[str] = []
    peligros_cat = {p.id: p for p in catalogo.peligros}
    controles_cat = {c.id: c for c in catalogo.controles}
    incidentes_cat = {i.id: i for i in catalogo.incidentes}
    resultado: dict[str, PeligroDetectado] = {}

    for pd in (bruto.peligros if bruto else []):
        if pd.peligro_id not in peligros_cat:
            descartes.append(f"peligro inexistente: {pd.peligro_id}")
            continue

        incidentes = []
        for iid in pd.incidentes_similares:
            if iid in incidentes_cat and iid in incidentes_vistos:
                incidentes.append(iid)
            else:
                descartes.append(f"incidente no devuelto por buscar_incidentes: {iid}")
        extras_permitidos = {incidentes_cat[i].control_fallido for i in incidentes} - {None}

        controles = []
        for cid in pd.controles:
            control = controles_cat.get(cid)
            if control is None:
                descartes.append(f"control inexistente: {cid}")
            elif tarea.tipo_tarea not in control.aplica_a and cid not in extras_permitidos:
                descartes.append(f"control que no aplica al tipo de tarea y sin incidente que lo respalde: {cid}")
            else:
                controles.append(cid)

        actual = resultado.setdefault(
            pd.peligro_id, PeligroDetectado(peligro_id=pd.peligro_id, justificacion=pd.justificacion))
        actual.controles += [c for c in controles if c not in actual.controles]
        actual.incidentes_similares += [i for i in incidentes if i not in actual.incidentes_similares]

    for control in catalogo.controles:
        if tarea.tipo_tarea not in control.aplica_a:
            continue
        if control.peligro_id not in peligros_cat:
            descartes.append(f"control {control.id} apunta a un peligro inexistente: {control.peligro_id}")
            continue
        actual = resultado.setdefault(control.peligro_id, PeligroDetectado(
            peligro_id=control.peligro_id,
            justificacion="Control exigido por el catálogo para este tipo de tarea.",
        ))
        if control.id not in actual.controles:
            actual.controles.append(control.id)

    for d in descartes:
        log.warning("riesgo: descartado %s", d)
    return EvaluacionRiesgo(peligros=list(resultado.values())), descartes


def _resumen_incidente(i: Incidente) -> dict[str, Any]:
    return {
        "id": i.id,
        "riesgo_critico": i.riesgo_critico,
        "nivel_potencial": i.nivel_potencial,
        "descripcion": i.descripcion[:200],
        "control_fallido": i.control_fallido,
    }


def _prompt_usuario(tarea: Tarea, catalogo: Catalogo, conocimiento: str) -> str:
    tipo = next((t for t in catalogo.tipos_tarea if t.id == tarea.tipo_tarea), None)
    # El tipo de tarea no declara peligros: salen de los controles que le aplican.
    del_tipo = {c.peligro_id for c in catalogo.controles if tarea.tipo_tarea in c.aplica_a}
    datos = {
        "tarea": {"tipo": tarea.tipo_tarea, "nombre_del_tipo": tipo.nombre if tipo else None,
                  "descripcion": tarea.descripcion, "zona": tarea.zona,
                  "turno": tarea.turno.model_dump(mode="json")},
        "peligros_del_tipo_de_tarea": [
            {"id": p.id, "nombre": p.nombre} for p in catalogo.peligros if p.id in del_tipo],
        "otros_peligros_del_catalogo": [
            {"id": p.id, "nombre": p.nombre} for p in catalogo.peligros if p.id not in del_tipo],
        "controles_del_catalogo": [
            {"id": c.id, "nombre": c.nombre, "peligro_id": c.peligro_id,
             "aplica_al_tipo_de_tarea": tarea.tipo_tarea in c.aplica_a}
            for c in catalogo.controles],
    }
    texto = json.dumps(datos, ensure_ascii=False, indent=2)
    if conocimiento:
        texto += f"\n\nBase de conocimiento (resúmenes con cita):\n{conocimiento}"
    return texto


async def evaluar_riesgo(
    tarea: Tarea,
    catalogo: Catalogo,
    emitir: Emitir,
    *,
    escenario_id: str | None = None,
    buscar: Callable[..., Any] | None = None,
    cliente: ClienteLLM | None = None,
    conocimiento: str | None = None,
) -> EvaluacionRiesgo:
    """Evalúa los peligros y controles de la tarea y emite los eventos del agente."""
    buscar = buscar or _stubs.buscar_incidentes
    cliente = cliente or get_cliente()
    if conocimiento is None:
        conocimiento = cargar_conocimiento()
    incidentes_vistos: set[str] = set()

    await emitir(TipoEvento.AGENTE_INICIADO, ACTOR, {"agente": ACTOR})

    async def herramienta_buscar(args: dict[str, Any]) -> str:
        entrada = {k: args.get(k) for k in ("equipo", "actividad", "riesgo_critico") if args.get(k)}
        inicio = time.perf_counter()
        encontrados = buscar(catalogo, **entrada, limite=LIMITE_INCIDENTES)
        if inspect.isawaitable(encontrados):
            encontrados = await encontrados
        incidentes_vistos.update(i.id for i in encontrados)
        traza = TraceHerramienta(
            nombre="buscar_incidentes", entrada=entrada,
            salida_resumen=f"{len(encontrados)} incidente(s): {', '.join(i.id for i in encontrados) or 'ninguno'}",
            duracion_ms=int((time.perf_counter() - inicio) * 1000),
        )
        await emitir(TipoEvento.AGENTE_HERRAMIENTA, ACTOR,
                     {"agente": ACTOR, "trace": traza.model_dump(mode="json")})
        return json.dumps([_resumen_incidente(i) for i in encontrados], ensure_ascii=False)

    herramientas = [Herramienta(
        nombre="buscar_incidentes",
        descripcion="Busca hasta 5 incidentes similares del catálogo, ordenados por relevancia.",
        parametros=PARAMETROS_BUSCAR,
        funcion=herramienta_buscar,
    )]

    bruto: EvaluacionRiesgo | None = None
    degradado: str | None = None
    try:
        bruto = await cliente.completar(
            agente=NOMBRE_LLM,
            sistema=SISTEMA,
            usuario=_prompt_usuario(tarea, catalogo, conocimiento),
            esquema=EvaluacionRiesgo,
            herramientas=herramientas,
            escenario_id=escenario_id,
            contexto_fake={"catalogo": catalogo, "tarea": tarea},
        )
    except LLMError as e:
        degradado = str(e)
        log.error("riesgo: LLM no disponible, se usa el checklist base del catálogo: %s", e)

    evaluacion, descartes = filtrar_y_completar(bruto, tarea, catalogo, incidentes_vistos)

    resumen = f"{len(evaluacion.peligros)} peligro(s) y {len(controles_exigidos(evaluacion))} control(es) exigido(s)."
    if degradado:
        resumen += f" LLM no disponible ({degradado}); se aplicó el checklist base del catálogo."
    if descartes:
        resumen += f" Se descartaron {len(descartes)} referencia(s) inválida(s) del LLM."
    await emitir(TipoEvento.AGENTE_COMPLETADO, ACTOR, {
        "agente": ACTOR, "resumen": resumen, "evaluacion": evaluacion.model_dump(mode="json")})
    return evaluacion
