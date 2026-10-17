"""Alternativas ante un conflicto (P2): el LLM propone, el código valida, las herramientas verifican.

El LLM solo puede combinar tres tipos de cambio sobre la asignación original y los IDs deben
existir en el catálogo (RF-F2-02). Ningún cambio puede quitar o relajar un requisito (RF-F2-05):
la re-verificación siempre evalúa todos los requisitos del catálogo. El veredicto no sale de aquí.
"""
import json
import logging
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel, Field

from app.agents._contrato import Alternativa, Cambio, Catalogo, Tarea, TipoCambio, TurnoRef
from app.llm import ClienteLLM, ContextoFake, LLMError, get_cliente, registrar_fake

log = logging.getLogger("capataz.alternativas")

NOMBRE_LLM = "alternativas"
MAX_ALTERNATIVAS = 3
TIPOS_PERMITIDOS = {t.value for t in TipoCambio}

SISTEMA = """Eres el Agente de Alternativas de CAPATAZ. Una tarea minera tiene un conflicto: uno o más \
requisitos de controles críticos bloqueantes NO se cumplen. Propón hasta 3 alternativas de asignación. \
No decides si son seguras: el código las re-verificará con herramientas.

Reglas:
- Cada alternativa es una lista de cambios sobre la asignación original. Tipos permitidos, y solo estos:
  * reprogramar_turno: desde = turno actual, hacia = otro turno, ambos con formato AAAA-MM-DD/dia o AAAA-MM-DD/noche.
  * equipo_equivalente: desde = ID de un equipo hoy asignado, hacia = ID de otro equipo del catálogo.
  * certificacion_equivalente: desde = ID de una persona hoy asignada, hacia = ID de otra persona del catálogo.
- Usa SOLO IDs de las listas que se te entregan. No inventes IDs.
- Una alternativa puede combinar varios cambios. No puedes quitar ni relajar ningún requisito.
- Si recibes `motivos_previos`, evita repetir lo que ya falló y corrige la causa.
- `explicacion`: máximo 2 frases en lenguaje claro: por qué es razonable y qué se sacrifica.
- Termina siempre llamando a la función `responder`."""


class CambioPropuesto(BaseModel):
    tipo: str
    desde: str
    hacia: str
    motivo: str = ""


class AlternativaPropuesta(BaseModel):
    cambios: list[CambioPropuesto] = Field(default_factory=list)
    explicacion: str = ""


class PropuestaAlternativas(BaseModel):
    alternativas: list[AlternativaPropuesta] = Field(default_factory=list)


# -- turnos y cambios -------------------------------------------------------------------

def formatear_turno(turno: TurnoRef) -> str:
    return f"{turno.fecha.isoformat()}/{turno.turno}"


def parsear_turno(texto: str) -> TurnoRef:
    fecha, _, franja = texto.partition("/")
    return TurnoRef(fecha=date.fromisoformat(fecha), turno=franja)  # type: ignore[arg-type]


def aplicar_cambios(tarea: Tarea, cambios: list[Cambio]) -> Tarea:
    """La tarea con los cambios aplicados; no modifica la original."""
    asignacion = tarea.asignacion.model_copy(deep=True)
    turno = tarea.turno
    for c in cambios:
        if c.tipo == TipoCambio.REPROGRAMAR_TURNO:
            turno = parsear_turno(c.hacia)
        elif c.tipo == TipoCambio.EQUIPO_EQUIVALENTE:
            asignacion.equipos = [c.hacia if e == c.desde else e for e in asignacion.equipos]
        elif c.tipo == TipoCambio.CERTIFICACION_EQUIVALENTE:
            asignacion.personas = [c.hacia if p == c.desde else p for p in asignacion.personas]
    return tarea.model_copy(update={"turno": turno, "asignacion": asignacion})


def describir(cambios: list[Cambio]) -> str:
    return "; ".join(f"{c.tipo.value}: {c.desde} → {c.hacia}" for c in cambios)


def _error_en_cambios(p: AlternativaPropuesta, tarea: Tarea, catalogo: Catalogo) -> str | None:
    if not p.cambios:
        return "sin cambios"
    equipos = {e.id for e in catalogo.equipos}
    personas = {x.id for x in catalogo.personas}
    for c in p.cambios:
        if c.tipo not in TIPOS_PERMITIDOS:
            return f"tipo de cambio no permitido: {c.tipo}"
        if c.tipo == TipoCambio.REPROGRAMAR_TURNO:
            if c.desde != formatear_turno(tarea.turno):
                return f"el turno de origen {c.desde} no es el turno actual"
            try:
                parsear_turno(c.hacia)
            except ValueError:
                return f"turno inválido: {c.hacia}"
            if c.hacia == c.desde:
                return "reprograma al mismo turno"
        elif c.tipo == TipoCambio.EQUIPO_EQUIVALENTE:
            if c.desde not in tarea.asignacion.equipos:
                return f"el equipo {c.desde} no está asignado"
            if c.hacia not in equipos:
                return f"equipo inexistente: {c.hacia}"
            if c.hacia in tarea.asignacion.equipos:
                return f"el equipo {c.hacia} ya está asignado"
        else:
            if c.desde not in tarea.asignacion.personas:
                return f"la persona {c.desde} no está asignada"
            if c.hacia not in personas:
                return f"persona inexistente: {c.hacia}"
            if c.hacia in tarea.asignacion.personas:
                return f"la persona {c.hacia} ya está asignada"
    return None


def validar_propuestas(
    propuestas: list[AlternativaPropuesta], tarea: Tarea, catalogo: Catalogo, ronda: int, vistas: set[str],
) -> tuple[list[Alternativa], list[str]]:
    """Alternativas válidas (máx. 3) y los motivos de descarte. `vistas` evita repetir entre rondas."""
    validas: list[Alternativa] = []
    descartes: list[str] = []
    for i, p in enumerate(propuestas, start=1):
        if len(validas) == MAX_ALTERNATIVAS:
            break
        error = _error_en_cambios(p, tarea, catalogo)
        if error:
            descartes.append(f"alternativa {i} descartada: {error}")
            continue
        cambios = [Cambio(tipo=TipoCambio(c.tipo), desde=c.desde, hacia=c.hacia, motivo=c.motivo) for c in p.cambios]
        firma = "|".join(sorted(f"{c.tipo.value}:{c.desde}>{c.hacia}" for c in cambios))
        if firma in vistas:
            descartes.append(f"alternativa {i} descartada: repite una ya evaluada")
            continue
        vistas.add(firma)
        validas.append(Alternativa(ronda=ronda, cambios=cambios, explicacion=p.explicacion))  # type: ignore[arg-type]
    for d in descartes:
        log.warning("alternativas ronda %d: %s", ronda, d)
    return validas, descartes


# -- LLM ----------------------------------------------------------------------------------

def _usuario(tarea: Tarea, catalogo: Catalogo, fallos: list[dict[str, Any]], ronda: int,
             motivos_previos: list[str]) -> str:
    datos = {
        "ronda": ronda,
        "tarea": {"tipo": tarea.tipo_tarea, "descripcion": tarea.descripcion, "turno": formatear_turno(tarea.turno),
                  "asignacion_actual": tarea.asignacion.model_dump(mode="json")},
        "requisitos_que_no_se_cumplen": fallos,
        "motivos_previos": motivos_previos,
        "personas_del_catalogo": [
            {"id": p.id, "rol": p.rol,
             "certificaciones": [{"codigo": c.codigo, "vence": c.vence.isoformat()} for c in p.certificaciones],
             "turnos_disponibles": [formatear_turno(t) for t in p.turnos]}
            for p in catalogo.personas],
        "equipos_del_catalogo": [
            {"id": e.id, "tipo": e.tipo_equipo, "estado": e.estado.value, "tipos_equivalentes": e.tipos_equivalentes,
             "turnos_en_mantenimiento": [formatear_turno(t) for t in e.mantenimiento]}
            for e in catalogo.equipos],
    }
    return json.dumps(datos, ensure_ascii=False, indent=2)


async def proponer_alternativas(
    tarea: Tarea,
    catalogo: Catalogo,
    fallos: list[dict[str, Any]],
    ronda: int,
    motivos_previos: list[str],
    vistas: set[str],
    *,
    escenario_id: str | None = None,
    cliente: ClienteLLM | None = None,
) -> tuple[list[Alternativa], list[str]]:
    """Pide propuestas al LLM y las filtra. Si el LLM falla no hay alternativas (nunca se inventan)."""
    cliente = cliente or get_cliente()
    try:
        propuesta = await cliente.completar(
            agente=NOMBRE_LLM,
            sistema=SISTEMA,
            usuario=_usuario(tarea, catalogo, fallos, ronda, motivos_previos),
            esquema=PropuestaAlternativas,
            escenario_id=escenario_id,
            contexto_fake={"catalogo": catalogo, "tarea": tarea, "fallos": fallos, "ronda": ronda,
                           "motivos_previos": motivos_previos},
        )
    except LLMError as e:
        log.error("alternativas ronda %d: LLM no disponible: %s", ronda, e)
        return [], [f"LLM no disponible: {e}"]
    return validar_propuestas(propuesta.alternativas, tarea, catalogo, ronda, vistas)


# -- modo fake -----------------------------------------------------------------------------
# Propone con heurísticas sobre el catálogo, sin mirar vigencias ni disponibilidad: como un LLM
# que "cree" que sirven. El veredicto lo dan las herramientas.

def _cambios_de_reemplazo(tarea: Tarea, catalogo: Catalogo, fallos: list[dict[str, Any]], indice: int) -> list[dict]:
    equipos = {e.id: e for e in catalogo.equipos}
    cambios: list[dict] = []
    usados: set[str] = set(tarea.asignacion.equipos) | set(tarea.asignacion.personas)
    for f in fallos:
        if f["tipo"] == "equipo":
            candidatos = sorted(
                (e for e in catalogo.equipos if e.id not in usados
                 and (e.tipo_equipo == f["tipo_equipo"] or f["tipo_equipo"] in e.tipos_equivalentes)),
                key=lambda e: e.estado.value != "operativo")
            desde = next((x for x in tarea.asignacion.equipos
                          if x in equipos and equipos[x].tipo_equipo == f["tipo_equipo"]),
                         tarea.asignacion.equipos[0] if tarea.asignacion.equipos else None)
            if candidatos and desde and desde not in {c["desde"] for c in cambios}:
                hacia = candidatos[min(indice, len(candidatos) - 1)]
                usados.add(hacia.id)
                cambios.append({"tipo": "equipo_equivalente", "desde": desde, "hacia": hacia.id,
                                "motivo": f"Equipo de tipo {f['tipo_equipo']} o equivalente"})
        elif f["tipo"] == "competencia":
            codigos = {f["certificacion"], *f.get("certificaciones_equivalentes", [])}
            candidatos = sorted(
                (p for p in catalogo.personas if p.id not in usados and any(c.codigo in codigos for c in p.certificaciones)),
                key=lambda p: -max(c.vence.toordinal() for c in p.certificaciones if c.codigo in codigos))
            desde = next((x for x in tarea.asignacion.personas if x not in {c["desde"] for c in cambios}), None)
            if candidatos and desde:
                hacia = candidatos[min(indice, len(candidatos) - 1)]
                usados.add(hacia.id)
                cambios.append({"tipo": "certificacion_equivalente", "desde": desde, "hacia": hacia.id,
                                "motivo": f"Cuenta con la certificación {f['certificacion']} o una equivalente"})
    return cambios


def _cambio_turno(tarea: Tarea, dias: int) -> dict:
    nuevo = TurnoRef(fecha=tarea.turno.fecha + timedelta(days=dias), turno=tarea.turno.turno)
    return {"tipo": "reprogramar_turno", "desde": formatear_turno(tarea.turno), "hacia": formatear_turno(nuevo),
            "motivo": "Esperar a que el recurso esté disponible"}


def _explicar(cambios: list[dict]) -> str:
    partes = []
    for c in cambios:
        if c["tipo"] == "reprogramar_turno":
            partes.append(f"mover la tarea de {c['desde']} a {c['hacia']}")
        elif c["tipo"] == "equipo_equivalente":
            partes.append(f"usar {c['hacia']} en lugar de {c['desde']}")
        else:
            partes.append(f"asignar a {c['hacia']} en lugar de {c['desde']}")
    return "Propuesta: " + "; ".join(partes) + ". Se sacrifica el plan original; la verificación decide si es seguro."


def _fake_alternativas(ctx: ContextoFake) -> dict[str, Any]:
    c = ctx.contexto
    catalogo, tarea, fallos, ronda = c["catalogo"], c["tarea"], c["fallos"], c["ronda"]
    if ronda == 1:
        opciones = [_cambios_de_reemplazo(tarea, catalogo, fallos, i) for i in (0, 1)]
    else:
        opciones = [[_cambio_turno(tarea, 1)] + _cambios_de_reemplazo(tarea, catalogo, fallos, 0),
                    [_cambio_turno(tarea, 2)] + _cambios_de_reemplazo(tarea, catalogo, fallos, 1)]
    unicas = [o for i, o in enumerate(opciones) if o and o not in opciones[:i]]
    return {"alternativas": [{"cambios": o, "explicacion": _explicar(o)} for o in unicas]}


registrar_fake(NOMBRE_LLM, _fake_alternativas)
