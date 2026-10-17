import asyncio
from datetime import date

import pytest
from pydantic_core import to_jsonable_python

from app.agents._contrato import (
    ACTOR_RIESGO, Catalogo, Control, Evento, Fuente, Incidente, Peligro, Requisito, Tarea, TipoEvento, TipoTarea,
    TurnoRef, validar_payload,
)
from app.seed_juguete import catalogo_juguete
from app.agents.riesgo import cargar_conocimiento, controles_exigidos, evaluar_riesgo
from app.llm import ClienteLLM, registrar_fake

SIM = Fuente(tipo="simulado", referencia="seed de prueba")


def control(id_, peligro, aplica):
    return Control(id=id_, nombre=f"Control {id_}", peligro_id=peligro, aplica_a=aplica, fuente=SIM,
                   requisitos=[Requisito(id=f"{id_}-R1", tipo="equipo", descripcion="x", tipo_equipo="jumbo")])


@pytest.fixture
def catalogo():
    return Catalogo(
        peligros=[Peligro(id="P1", nombre="Caída de rocas"),
                  Peligro(id="P2", nombre="Equipo móvil"),
                  Peligro(id="P3", nombre="Trabajo en altura")],
        tipos_tarea=[TipoTarea(id="T1", nombre="Sostenimiento"),
                     TipoTarea(id="T2", nombre="Mantenimiento en altura")],
        controles=[control("C1", "P1", ["T1"]), control("C2", "P2", ["T1"]), control("C3", "P3", ["T2"])],
        incidentes=[Incidente(id="I1", fecha=date(2025, 5, 4), riesgo_critico="caída de rocas",
                              nivel_potencial="alto", descripcion="Caída de roca en galería", control_fallido="C3"),
                    Incidente(id="I2", fecha=date(2025, 6, 1), riesgo_critico="equipo móvil",
                              nivel_potencial="medio", descripcion="Colisión de equipo")],
    )


@pytest.fixture
def tarea():
    return Tarea(id="TA1", tipo_tarea="T1", descripcion="roca inestable en galería 3", zona="G3",
                 turno=TurnoRef(fecha=date(2026, 10, 20), turno="dia"))


class Emisor:
    def __init__(self):
        self.eventos = []

    async def __call__(self, tipo, actor, payload):
        self.eventos.append((tipo, actor, payload))
        evento = Evento(run_id="r", seq=len(self.eventos), tipo=tipo, actor=actor,
                        payload=to_jsonable_python(payload))
        validar_payload(evento)  # igual que el runtime de P1: un payload inválido es un bug
        return evento

    @property
    def tipos(self):
        return [t for t, _, _ in self.eventos]


def buscar_de(catalogo, *ids):
    def buscar(cat, equipo=None, actividad=None, riesgo_critico=None, limite=5):
        return [i for i in cat.incidentes if i.id in ids][:limite]
    return buscar


def evaluar(tarea, catalogo, buscar=None, escenario_id=None, cliente=None):
    emisor = Emisor()
    evaluacion = asyncio.run(evaluar_riesgo(
        tarea, catalogo, emisor, escenario_id=escenario_id, buscar=buscar,
        cliente=cliente or ClienteLLM(modo="fake"), conocimiento=""))
    return evaluacion, emisor


def ids(evaluacion):
    return {p.peligro_id: p for p in evaluacion.peligros}


# -- modo fake: camino feliz ---------------------------------------------------------

def test_fake_exige_los_controles_del_tipo_de_tarea_y_emite_los_eventos_del_agente(tarea, catalogo):
    evaluacion, emisor = evaluar(tarea, catalogo, buscar=buscar_de(catalogo, "I2"))
    assert controles_exigidos(evaluacion) == ["C1", "C2"]
    assert emisor.tipos[0] == TipoEvento.AGENTE_INICIADO
    assert emisor.tipos[-1] == TipoEvento.AGENTE_COMPLETADO
    assert TipoEvento.AGENTE_HERRAMIENTA in emisor.tipos
    assert {a for _, a, _ in emisor.eventos} == {ACTOR_RIESGO}


def test_el_control_fallido_de_un_incidente_similar_se_suma_al_checklist(tarea, catalogo):
    evaluacion, _ = evaluar(tarea, catalogo, buscar=buscar_de(catalogo, "I1"))  # I1 falló en C3, que no aplica al tipo
    assert controles_exigidos(evaluacion) == ["C1", "C3", "C2"]


def test_las_trazas_describen_la_herramienta_usada(tarea, catalogo):
    _, emisor = evaluar(tarea, catalogo, buscar=buscar_de(catalogo, "I1"))
    trazas = [p["trace"] for t, _, p in emisor.eventos if t == TipoEvento.AGENTE_HERRAMIENTA]
    assert trazas and all(t["nombre"] == "buscar_incidentes" and t["salida_resumen"] for t in trazas)


def test_incidentes_citados_son_los_que_devolvio_la_herramienta(tarea, catalogo):
    evaluacion, _ = evaluar(tarea, catalogo, buscar=buscar_de(catalogo, "I2"))
    citados = {i for p in evaluacion.peligros for i in p.incidentes_similares}
    assert citados == {"I2"}


def test_con_el_stub_de_p3_no_hay_incidentes_pero_si_controles(tarea, catalogo):
    evaluacion, _ = evaluar(tarea, catalogo)
    assert controles_exigidos(evaluacion) == ["C1", "C2"]
    assert all(p.incidentes_similares == [] for p in evaluacion.peligros)


def test_funciona_con_el_catalogo_real_de_p1_y_sus_eventos_validan_contra_el_contrato():
    cat = catalogo_juguete()
    evaluacion, emisor = evaluar(cat.escenarios[0].tarea, cat, buscar=buscar_de(cat, "INC-JUG-01"))
    assert controles_exigidos(evaluacion) == ["CTL-JUG-01", "CTL-JUG-02"]
    assert [p.peligro_id for p in evaluacion.peligros] == ["PEL-JUG-01"]
    assert evaluacion.peligros[0].incidentes_similares == ["INC-JUG-01"]
    assert emisor.tipos == [TipoEvento.AGENTE_INICIADO, TipoEvento.AGENTE_HERRAMIENTA, TipoEvento.AGENTE_COMPLETADO]


# -- filtro post-LLM -------------------------------------------------------------------

def test_ids_inventados_se_descartan_y_los_controles_base_se_mantienen(tarea, catalogo):
    registrar_fake("riesgo", lambda ctx: {"peligros": [
        {"peligro_id": "P1", "justificacion": "x", "controles": ["C99"], "incidentes_similares": ["I99"]},
        {"peligro_id": "P-INVENTADO", "justificacion": "y", "controles": ["C1"]},
    ]}, escenario_id="AMBIGUO")
    evaluacion, emisor = evaluar(tarea, catalogo, buscar=buscar_de(catalogo, "I1"), escenario_id="AMBIGUO")
    assert "P-INVENTADO" not in ids(evaluacion)
    assert set(controles_exigidos(evaluacion)) <= {c.id for c in catalogo.controles}
    assert controles_exigidos(evaluacion) == ["C1", "C2"]
    assert "descartaron 3" in emisor.eventos[-1][2]["resumen"]


def test_el_llm_no_puede_omitir_un_control_del_tipo_de_tarea(tarea, catalogo):
    registrar_fake("riesgo", lambda ctx: {"peligros": []}, escenario_id="VACIO")
    evaluacion, _ = evaluar(tarea, catalogo, escenario_id="VACIO")
    assert controles_exigidos(evaluacion) == ["C1", "C2"]


def test_un_control_ajeno_al_tipo_pasa_solo_si_lo_respalda_un_incidente_devuelto(tarea, catalogo):
    async def con_busqueda(ctx):
        await ctx.llamar("buscar_incidentes", riesgo_critico="desprendimiento_rocas")
        return {"peligros": [
            {"peligro_id": "P3", "justificacion": "x", "controles": ["C3"], "incidentes_similares": ["I1"]}]}

    registrar_fake("riesgo", con_busqueda, escenario_id="EXTRA")

    con_incidente, _ = evaluar(tarea, catalogo, buscar=buscar_de(catalogo, "I1"), escenario_id="EXTRA")
    assert controles_exigidos(con_incidente) == ["C3", "C1", "C2"]

    sin_incidente, _ = evaluar(tarea, catalogo, buscar=buscar_de(catalogo), escenario_id="EXTRA")
    assert "C3" not in controles_exigidos(sin_incidente)


def test_un_incidente_real_que_no_se_busco_se_descarta(tarea, catalogo):
    async def con_busqueda(ctx):
        await ctx.llamar("buscar_incidentes", riesgo_critico="equipo_movil")
        return {"peligros": [
            {"peligro_id": "P1", "justificacion": "x", "controles": ["C1"], "incidentes_similares": ["I1", "I2"]}]}

    registrar_fake("riesgo", con_busqueda, escenario_id="NOBUSCADO")
    evaluacion, _ = evaluar(tarea, catalogo, buscar=buscar_de(catalogo, "I2"), escenario_id="NOBUSCADO")
    assert ids(evaluacion)["P1"].incidentes_similares == ["I2"]


# -- fallo del LLM ---------------------------------------------------------------------

def test_si_el_llm_falla_se_aplica_el_checklist_base_y_se_informa(tarea, catalogo):
    cliente_roto = type("Roto", (), {"completar": staticmethod(_siempre_falla)})()
    evaluacion, emisor = evaluar(tarea, catalogo, cliente=cliente_roto)
    assert controles_exigidos(evaluacion) == ["C1", "C2"]
    assert "LLM no disponible" in emisor.eventos[-1][2]["resumen"]
    assert emisor.tipos[-1] == TipoEvento.AGENTE_COMPLETADO


async def _siempre_falla(**kwargs):
    from app.llm import LLMError
    raise LLMError("sin red")


# -- base de conocimiento ----------------------------------------------------------------

def test_cargar_conocimiento_lee_los_md_y_tolera_que_no_exista(tmp_path):
    assert cargar_conocimiento(tmp_path / "no-existe") == ""
    (tmp_path / "a.md").write_text("fuente: simulado\nresumen A", encoding="utf-8")
    (tmp_path / "b.txt").write_text("ignorado", encoding="utf-8")
    texto = cargar_conocimiento(tmp_path)
    assert "resumen A" in texto and "ignorado" not in texto
    assert len(cargar_conocimiento(tmp_path, max_chars=10)) == 10
