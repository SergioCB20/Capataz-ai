"""Evaluación de detección sobre datos simulados (RF-F3-21, RF-F3-22). La usa `scripts/evaluar.py`.

Cada caso (`CasoEvaluacion`) se ejecuta con el Supervisor de P2, las herramientas reales de P3 y el
LLM en modo fake, dos veces:
  - «checklist base»: sin `buscar_incidentes` (solo los controles del catálogo para el tipo de tarea);
  - «completa»: con `buscar_incidentes`, que puede sumar controles por el patrón de incidentes.
Una falla inyectada está **detectada** si el estado de la primera pasada coincide con el esperado del caso
(que fija el equipo, no el LLM). Se atribuye al checklist base si ya lo detecta sin incidentes, y a los
incidentes si solo lo detecta la corrida completa. Un caso limpio es **falso positivo** si no sale como se
esperaba. El reporte no tiene fechas ni tiempos: dos ejecuciones dan el mismo resultado.
"""
import json

from app.agents import _p3
from app.agents.supervisor import Dependencias, ejecutar_run
from app.contract import CasoEvaluacion, Catalogo, EstadoControl, Run, TipoEvento
from app.llm import ClienteLLM

ENCABEZADO = (
    "DATOS SIMULADOS. Esta métrica mide si el sistema detecta las fallas que se le inyectan en datos "
    "sintéticos; no demuestra que reduzca accidentes reales."
)


async def _sin_incidentes(catalogo, **_):
    return []


async def _correr(catalogo: Catalogo, caso: CasoEvaluacion, buscar) -> dict:
    """Ejecuta un caso y devuelve su primera pasada y su estado final."""
    eventos: list[tuple[TipoEvento, dict]] = []

    async def emitir(tipo, actor, payload):
        eventos.append((tipo, json.loads(json.dumps(payload, default=lambda o: o.model_dump(mode="json")))))

    deps = Dependencias(verificar_personal=_p3.verificar_personal, verificar_equipo=_p3.verificar_equipo,
                        buscar=buscar, cliente=ClienteLLM(modo="fake"))
    try:
        await ejecutar_run(Run(id=f"eval-{caso.id}", tarea=caso.tarea), catalogo, emitir, deps=deps)
    except Exception as e:  # un caso que falla no debe tumbar la evaluación
        return {"primera_pasada": "ERROR", "final": "ERROR", "con_fallo": [], "error": f"{type(e).__name__}: {e}"}

    consolidado = next(p for t, p in eventos if t == TipoEvento.SUPERVISOR_CONSOLIDADO)
    listo = next((p for t, p in reversed(eventos) if t == TipoEvento.PLAN_LISTO), None)
    candidato = (listo["planes_alternativos"] or [listo["plan"]])[0] if listo else None
    return {
        "primera_pasada": consolidado["estado_sistema"],
        "final": candidato["estado_sistema"] if candidato else "SIN_PLAN",
        "con_fallo": sorted(r["control_id"] for r in consolidado["resultados"] if r["estado"] != EstadoControl.CUMPLE),
    }


def _clasificar(caso: CasoEvaluacion, base: str, completa: str) -> str:
    esperado = caso.resultado_esperado.value
    if caso.falla_inyectada is None:
        return "limpio_correcto" if completa == esperado else "falso_positivo"
    if base == esperado:
        return "checklist"
    return "incidentes" if completa == esperado else "no_detectada"


async def evaluar(catalogo: Catalogo, casos: list[CasoEvaluacion]) -> dict:
    filas = []
    for caso in casos:
        base = await _correr(catalogo, caso, _sin_incidentes)
        completa = await _correr(catalogo, caso, _p3.buscar_incidentes)
        clase = _clasificar(caso, base["primera_pasada"], completa["primera_pasada"])
        fila = {
            "id": caso.id,
            "falla_inyectada": caso.falla_inyectada,
            "esperado": caso.resultado_esperado.value,
            "declarado_detectable_por": caso.detectable_por,
            "primera_pasada_checklist_base": base["primera_pasada"],
            "primera_pasada_completa": completa["primera_pasada"],
            "estado_final": completa["final"],
            "controles_con_fallo": completa["con_fallo"],
            "resultado": clase,
            "coincide_con_lo_declarado": caso.falla_inyectada is None or caso.detectable_por in (None, clase),
        }
        if "error" in completa:
            fila["error"] = completa["error"]
        filas.append(fila)

    con_falla = [f for f in filas if f["falla_inyectada"]]
    limpios = [f for f in filas if not f["falla_inyectada"]]
    por_via = {v: sum(f["resultado"] == v for f in con_falla) for v in ("checklist", "incidentes", "no_detectada")}
    detectadas = por_via["checklist"] + por_via["incidentes"]
    falsos = sum(f["resultado"] == "falso_positivo" for f in limpios)

    por_tipo: dict[str, dict] = {}
    for f in con_falla:
        t = por_tipo.setdefault(f["falla_inyectada"], {"casos": 0, "detectadas": 0, "por_checklist": 0, "por_incidentes": 0})
        t["casos"] += 1
        t["detectadas"] += f["resultado"] in ("checklist", "incidentes")
        t["por_checklist"] += f["resultado"] == "checklist"
        t["por_incidentes"] += f["resultado"] == "incidentes"

    return {
        "encabezado": ENCABEZADO,
        "resumen": {
            "casos": len(filas), "con_falla_inyectada": len(con_falla), "limpios": len(limpios),
            "detectadas": detectadas,
            "tasa_deteccion": round(detectadas / len(con_falla), 4) if con_falla else None,
            "detectadas_por_checklist_base": por_via["checklist"],
            "detectadas_por_incidentes": por_via["incidentes"],
            "no_detectadas": por_via["no_detectada"],
            "falsos_positivos": falsos,
            "tasa_falsos_positivos": round(falsos / len(limpios), 4) if limpios else None,
            "coinciden_con_lo_declarado": sum(f["coincide_con_lo_declarado"] for f in con_falla),
        },
        "por_tipo_de_falla": dict(sorted(por_tipo.items())),
        "casos": filas,
    }


def _pct(valor: float | None) -> str:
    return "n/d" if valor is None else f"{valor * 100:.1f} %"


def formatear_tabla(reporte: dict) -> str:
    r = reporte["resumen"]
    lineas = [reporte["encabezado"], "", "RESUMEN",
              f"  Casos: {r['casos']} ({r['con_falla_inyectada']} con falla inyectada, {r['limpios']} limpios)",
              f"  Fallas detectadas: {r['detectadas']} de {r['con_falla_inyectada']} ({_pct(r['tasa_deteccion'])})",
              f"    por checklist base: {r['detectadas_por_checklist_base']}",
              f"    por patrón de incidentes: {r['detectadas_por_incidentes']}",
              f"    no detectadas: {r['no_detectadas']}",
              f"  Falsos positivos: {r['falsos_positivos']} de {r['limpios']} limpios ({_pct(r['tasa_falsos_positivos'])})",
              f"  Coinciden con lo declarado en el caso: {r['coinciden_con_lo_declarado']} de {r['con_falla_inyectada']}",
              "", "FALLAS POR TIPO", f"  {'tipo':<38}{'casos':>6}{'detect.':>9}{'checklist':>11}{'incidentes':>12}"]
    for tipo, t in reporte["por_tipo_de_falla"].items():
        lineas.append(f"  {tipo:<38}{t['casos']:>6}{t['detectadas']:>9}{t['por_checklist']:>11}{t['por_incidentes']:>12}")
    lineas += ["", "CASOS", f"  {'id':<8}{'falla':<36}{'esperado':<16}{'base':<16}{'completa':<16}resultado"]
    for f in reporte["casos"]:
        lineas.append(f"  {f['id']:<8}{(f['falla_inyectada'] or '(limpio)'):<36}{f['esperado']:<16}"
                      f"{f['primera_pasada_checklist_base']:<16}{f['primera_pasada_completa']:<16}{f['resultado']}")
    return "\n".join(lineas)
