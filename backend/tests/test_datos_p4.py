"""Protegen los datos de la demo (`data/`, `knowledge/`): los mínimos de RF-F0-09 y que cada escenario
produzca el resultado para el que fue diseñado, con el Supervisor real y las herramientas de P3."""
import asyncio
import json
import re
from collections import Counter
from pathlib import Path

import pytest
from pydantic_core import to_jsonable_python

from app.agents import _p3
from app.agents.supervisor import Dependencias, confirmar_campo, ejecutar_run
from app.catalogo import cargar_catalogo_desde_dir
from app.contract import (
    CasoEvaluacion, ConfirmacionesCampo, EstadoSistema, Plan, RespuestaCampo, Run, TipoEvento, TipoFuente,
)
from app.evaluacion import evaluar
from app.llm import ClienteLLM

RAIZ = Path(__file__).resolve().parents[2]
CAT = cargar_catalogo_desde_dir(RAIZ / "data")
CASOS = [CasoEvaluacion.model_validate(c) for c in json.loads((RAIZ / "data" / "evaluacion.json").read_text("utf-8"))]
DEPS = Dependencias(verificar_personal=_p3.verificar_personal, verificar_equipo=_p3.verificar_equipo,
                    buscar=_p3.buscar_incidentes, cliente=ClienteLLM(modo="fake"))


def correr(escenario_id):
    eventos = []

    async def emitir(tipo, actor, payload):
        eventos.append((tipo, to_jsonable_python(payload)))

    run = Run(id=f"t-{escenario_id}", tarea=CAT.escenario(escenario_id).tarea, escenario_id=escenario_id)
    asyncio.run(ejecutar_run(run, CAT, emitir, deps=DEPS))
    return run, eventos


def de_tipo(eventos, tipo):
    return [p for t, p in eventos if t == tipo]


# -- mínimos de RF-F0-09 y RF-F0-16 --------------------------------------------------------------

def test_cumple_los_minimos_de_datos_semilla():
    assert (len(CAT.peligros), len(CAT.tipos_tarea), len(CAT.controles)) >= (3, 4, 6)
    assert len(CAT.personas) >= 8 and len(CAT.equipos) >= 8 and len(CAT.incidentes) >= 50
    assert [e.id for e in CAT.escenarios] == ["E1", "E2", "E2c", "E3"]
    assert all(c.fuente and c.requisitos and isinstance(c.bloqueante, bool) and c.aplica_a is not None
               for c in CAT.controles)


def test_todo_es_simulado_y_los_incidentes_cubren_cada_tipo_de_tarea():
    todo = [*CAT.peligros, *CAT.controles, *CAT.personas, *CAT.equipos, *CAT.incidentes]
    assert all(o.fuente.tipo == TipoFuente.SIMULADO for o in todo)
    por_tipo = Counter(i.tipo_tarea for i in CAT.incidentes)
    assert all(por_tipo[t.id] >= 3 for t in CAT.tipos_tarea)


def test_el_control_que_solo_llega_por_incidentes_existe_y_esta_fuera_de_la_lista_base():
    extra = CAT.control("C-SSO-PRESENTE")
    assert extra and extra.aplica_a == []
    assert any(i.control_fallido == "C-SSO-PRESENTE" for i in CAT.incidentes)


# -- cada escenario produce su resultado -------------------------------------------------------------------

def test_e1_es_un_caso_limpio_que_se_recomienda():
    _, ev = correr("E1")
    cons = de_tipo(ev, TipoEvento.SUPERVISOR_CONSOLIDADO)[0]
    assert cons["estado_sistema"] == "RECOMENDADO"
    assert {r["control_id"] for r in cons["resultados"]} == {"C-SOST-OPER", "C-SOST-EQ", "C-SSO-PRESENTE"}
    assert ev[-1][0] == TipoEvento.HUMANO_DECISION_REQUERIDA and ev[-1][1]["solo_rechazo"] is False


def test_e2_conflicto_una_alternativa_falla_y_otra_se_verifica():
    _, ev = correr("E2")
    assert de_tipo(ev, TipoEvento.SUPERVISOR_CONSOLIDADO)[0]["estado_sistema"] == "BLOQUEADO"
    causas = " ".join(c["causa"] for c in de_tipo(ev, TipoEvento.CONFLICTO_DETECTADO))
    assert "mantenimiento" in causas.lower() and "venció" in causas
    veredictos = [a["alternativa"] for a in de_tipo(ev, TipoEvento.CONFLICTO_ALTERNATIVA_VERIFICADA)]
    assert [v["cumple_bloqueantes"] for v in veredictos] == [False, True]
    assert "no está disponible" in veredictos[0]["motivo_fallo"]
    listo = de_tipo(ev, TipoEvento.PLAN_LISTO)[0]
    assert listo["plan"]["estado_sistema"] == "BLOQUEADO"
    assert listo["planes_alternativos"][0]["estado_sistema"] == "RECOMENDADO"
    assert listo["planes_alternativos"][0]["id"] == veredictos[1]["id"]
    assert ev[-1][1] == {"plan_id": veredictos[1]["id"], "solo_rechazo": False}


def test_e2c_pide_confirmacion_de_campo_y_al_confirmarla_se_recomienda():
    run, ev = correr("E2c")
    assert de_tipo(ev, TipoEvento.SUPERVISOR_CONSOLIDADO)[0]["estado_sistema"] == "REQUIERE_CAMPO"
    preguntas = de_tipo(ev, TipoEvento.HUMANO_CAMPO_REQUERIDO)[0]["preguntas"]
    assert [p["requisito_id"] for p in preguntas] == ["R-LOTO-APLICADO"] and "energía cero" in preguntas[0]["pregunta"]

    run.plan = Plan.model_validate(de_tipo(ev, TipoEvento.PLAN_LISTO)[0]["plan"])
    nuevos = []

    async def emitir(tipo, actor, payload):
        nuevos.append((tipo, to_jsonable_python(payload)))

    conf = ConfirmacionesCampo(respuestas=[RespuestaCampo(requisito_id="R-LOTO-APLICADO", cumple=True)])
    asyncio.run(confirmar_campo(run, CAT, conf, emitir, deps=DEPS))
    assert de_tipo(nuevos, TipoEvento.PLAN_LISTO)[0]["plan"]["estado_sistema"] == "RECOMENDADO"


def test_e3_agota_las_dos_rondas_y_queda_bloqueado_con_escalamiento():
    _, ev = correr("E3")
    assert [a["ronda"] for a in de_tipo(ev, TipoEvento.CONFLICTO_ALTERNATIVAS)] == [1, 2]
    assert not any(a["alternativa"]["cumple_bloqueantes"] for a in de_tipo(ev, TipoEvento.CONFLICTO_ALTERNATIVA_VERIFICADA))
    plan = de_tipo(ev, TipoEvento.PLAN_LISTO)[0]["plan"]
    assert plan["estado_sistema"] == "BLOQUEADO" and plan["escalamiento"] == CAT.escenario("E3").escalamiento
    assert ev[-1][1]["solo_rechazo"] is True


def test_los_escenarios_no_comparten_persona_y_turno_para_no_chocar_entre_si():
    usados = Counter((p, e.tarea.turno.fecha, e.tarea.turno.turno) for e in CAT.escenarios for p in e.tarea.asignacion.personas)
    assert max(usados.values()) == 1


def test_el_resultado_esperado_de_cada_escenario_coincide_con_su_primera_pasada():
    for escenario in CAT.escenarios:
        _, ev = correr(escenario.id)
        assert de_tipo(ev, TipoEvento.SUPERVISOR_CONSOLIDADO)[0]["estado_sistema"] == escenario.resultado_esperado.value


# -- evaluación (RF-F3-20) ------------------------------------------------------------------------------------------

def test_el_conjunto_de_evaluacion_cumple_lo_pedido():
    assert len(CASOS) >= 15 and len({c.id for c in CASOS}) == len(CASOS)
    assert sum(c.falla_inyectada is None for c in CASOS) >= 3                      # casos limpios
    assert sum(c.detectable_por == "incidentes" for c in CASOS) >= 3               # solo por patrón de incidentes
    assert all(c.falla_inyectada or c.detectable_por is None for c in CASOS)
    ids_escenario = {e.tarea.id for e in CAT.escenarios}
    assert not ({c.tarea.id for c in CASOS} & ids_escenario)


def test_el_sistema_detecta_lo_inyectado_en_los_casos_de_evaluacion():
    r = asyncio.run(evaluar(CAT, CASOS))["resumen"]
    assert r["no_detectadas"] == 0 and r["falsos_positivos"] == 0
    assert r["coinciden_con_lo_declarado"] == r["con_falla_inyectada"]
    assert r["detectadas_por_incidentes"] >= 3 and r["detectadas_por_checklist_base"] >= 10


# -- base de conocimiento --------------------------------------------------------------------------------------------

def test_cada_documento_de_conocimiento_tiene_fuente_url_y_pagina():
    archivos = sorted((RAIZ / "knowledge").glob("*.md"))
    assert len(archivos) == 5
    for archivo in archivos:
        encabezado = archivo.read_text("utf-8").split("---")[1]
        for campo in ("fuente:", "url:", "pagina:", "tipo:", "verificado:"):
            assert campo in encabezado, f"{archivo.name} no tiene {campo}"
        assert re.search(r"url: https://", encabezado)


def test_la_base_de_conocimiento_cabe_en_el_contexto_del_agente_riesgo():
    from app.agents.riesgo import MAX_CONOCIMIENTO, cargar_conocimiento
    texto = cargar_conocimiento(RAIZ / "knowledge", max_chars=10**9)
    assert 0 < len(texto) <= MAX_CONOCIMIENTO  # si no, el texto se cortaría


def test_no_se_repite_el_dato_que_no_se_pudo_verificar():
    # RT-10: «19 de 26» no figura en ninguno de los cinco PDFs oficiales; el dato verificado es el 83 %.
    todo = " ".join(a.read_text("utf-8") for a in (RAIZ / "knowledge").glob("*.md"))
    assert "19 de 26" not in todo and "83 %" in todo
