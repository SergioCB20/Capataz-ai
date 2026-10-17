from datetime import date

from p3_datos import DIA, NOCHE, catalogo_p3, tarea

from app.contract import EstadoEquipo, TurnoRef
from app.tools.equipo import cubre_tipo, estado_equipo
from app.tools.incidentes import buscar_incidentes, nivel_ordinal
from app.tools.personal import doble_asignacion, personal_disponible, verificar_certificacion

CAT = catalogo_p3()
persona = {p.id: p for p in CAT.personas}
equipo = {e.id: e for e in CAT.equipos}


# -- Personal ------------------------------------------------------------------------------

def test_personal_disponible_en_el_turno():
    assert {p.id for p in personal_disponible(CAT, DIA)} == {"PER-1", "PER-2", "PER-3", "PER-4", "PER-5"}
    assert {p.id for p in personal_disponible(CAT, NOCHE)} == {"PER-1", "PER-3", "PER-5"}
    assert personal_disponible(CAT, TurnoRef(fecha=date(2026, 10, 21), turno="dia")) == []


def test_certificacion_vigente_cuenta_y_deja_evidencia():
    h = verificar_certificacion(persona["PER-1"], ["SOST"], DIA.fecha)
    assert h.cumple and "vigente hasta el 01/03/2027" in h.detalle
    ev = h.evidencia[0]
    assert (ev.registro, ev.campo, ev.valor) == ("personas/PER-1", "certificaciones.SOST.vence", "2027-03-01")


def test_certificacion_vencida_no_cuenta():
    h = verificar_certificacion(persona["PER-2"], ["SOST"], DIA.fecha)
    assert not h.cumple and "venció el 30/09/2026" in h.detalle and h.evidencia


def test_la_vigencia_se_mide_a_la_fecha_del_turno_inclusive():
    assert verificar_certificacion(persona["PER-2"], ["SOST"], date(2026, 9, 30)).cumple      # el último día aún vale
    assert not verificar_certificacion(persona["PER-2"], ["SOST"], date(2026, 10, 1)).cumple  # al día siguiente, no


def test_sin_la_certificacion_pedida_no_cumple():
    h = verificar_certificacion(persona["PER-4"], ["SOST"], DIA.fecha)
    assert not h.cumple and "ninguna" in h.detalle
    assert verificar_certificacion(persona["PER-3"], ["SOST"], DIA.fecha).cumple is False  # solo tiene SOST-B
    assert verificar_certificacion(persona["PER-3"], ["SOST", "SOST-B"], DIA.fecha).cumple is True


def test_con_varias_coincidencias_se_evalua_la_de_mayor_vencimiento():
    p = persona["PER-1"].model_copy(update={"certificaciones": [
        persona["PER-1"].certificaciones[0].model_copy(update={"vence": date(2026, 1, 1)}),
        persona["PER-1"].certificaciones[0].model_copy(update={"vence": date(2027, 6, 1)})]})
    assert verificar_certificacion(p, ["SOST"], DIA.fecha).cumple


def test_doble_asignacion_con_otra_tarea_del_mismo_turno():
    # SC-OCUPA asigna a PER-5 el turno día.
    assert [t.id for t in doble_asignacion(CAT, "PER-5", tarea(["PER-5"], ["EQ-1"]))] == ["TA-OCUPA"]
    assert doble_asignacion(CAT, "PER-5", tarea(["PER-5"], ["EQ-1"], turno=NOCHE)) == []       # otro turno
    assert doble_asignacion(CAT, "PER-1", tarea(["PER-1"], ["EQ-1"])) == []                    # otra persona
    assert doble_asignacion(CAT, "PER-5", tarea(["PER-5"], ["EQ-1"], id_="TA-OCUPA")) == []    # no se compara consigo misma


# -- Equipo ----------------------------------------------------------------------------------

def test_cubre_tipo_estricto_ignora_los_equivalentes():
    assert cubre_tipo(equipo["EQ-1"], "empernador", False).cumple
    h = cubre_tipo(equipo["EQ-3"], "empernador", False)
    assert not h.cumple and "perforadora" in h.detalle  # primera pasada: los tipos_equivalentes no cuentan


def test_cubre_tipo_con_equivalencias_solo_en_alternativas():
    h = cubre_tipo(equipo["EQ-3"], "empernador", True)
    assert h.cumple and "equivalente" in h.detalle
    assert not cubre_tipo(equipo["EQ-4"], "empernador", True).cumple  # sin relación declarada


def test_estado_operativo_y_disponible():
    h = estado_equipo(equipo["EQ-1"], DIA)
    assert h.cumple and h.evidencia[0].registro == "equipos/EQ-1" and h.evidencia[0].valor == "operativo"


def test_equipo_en_mantenimiento_no_cumple_con_su_evidencia():
    h = estado_equipo(equipo["EQ-2"], DIA)
    assert not h.cumple and "mantenimiento" in h.detalle
    assert (h.evidencia[0].campo, h.evidencia[0].valor) == ("estado", "mantenimiento")


def test_fuera_de_servicio_no_cumple():
    e = equipo["EQ-1"].model_copy(update={"estado": EstadoEquipo.FUERA_SERVICIO})
    assert "fuera de servicio" in estado_equipo(e, DIA).detalle


def test_mantenimiento_programado_solo_afecta_a_ese_turno():
    assert estado_equipo(equipo["EQ-3"], DIA).cumple
    h = estado_equipo(equipo["EQ-3"], NOCHE)
    assert not h.cumple and "programado" in h.detalle and h.evidencia[0].campo == "mantenimiento"


# -- buscar_incidentes ---------------------------------------------------------------------------

def ids(resultado):
    return [i.id for i in resultado]


def test_sostenimiento_en_roca_inestable_devuelve_primero_caida_de_rocas():
    r = buscar_incidentes(CAT, equipo="empernador", actividad="sostenimiento", riesgo_critico="Caída de rocas")
    assert ids(r)[:2] == ["INC-1", "INC-4"]           # 3 coincidencias; V antes que II
    assert all("roca" in i.riesgo_critico for i in r[:3])
    assert "INC-6" not in ids(r)                       # el de ruido no coincide con nada


def test_ignora_tildes_mayusculas_y_plurales():
    assert ids(buscar_incidentes(CAT, riesgo_critico="CAIDA DE ROCAS"))[:1] == ["INC-1"]
    assert "INC-5" in ids(buscar_incidentes(CAT, equipo="Plataformas"))


def test_prioridad_por_coincidencias_y_luego_por_nivel_potencial():
    r = buscar_incidentes(CAT, actividad="mantenimiento en altura", riesgo_critico="trabajo en altura")
    assert ids(r) == ["INC-5", "INC-3"]  # ambos con 2 coincidencias; VI antes que III


def test_maximo_cinco_resultados():
    assert len(buscar_incidentes(CAT, riesgo_critico="caída de rocas altura ruido", limite=50)) <= 5
    mas = CAT.model_copy(update={"incidentes": [CAT.incidentes[0].model_copy(update={"id": f"X-{n}"}) for n in range(9)]})
    assert len(buscar_incidentes(mas, equipo="empernador", limite=50)) == 5
    assert len(buscar_incidentes(mas, equipo="empernador", limite=2)) == 2
    assert buscar_incidentes(mas, equipo="empernador", limite=0) == []


def test_sin_coincidencias_devuelve_vacio_y_sin_criterios_ordena_por_nivel():
    assert buscar_incidentes(CAT, equipo="excavadora", actividad="voladura") == []
    assert ids(buscar_incidentes(CAT))[:2] == ["INC-5", "INC-1"]


def test_resultado_determinista():
    a = ids(buscar_incidentes(CAT, actividad="sostenimiento"))
    assert a == ids(buscar_incidentes(CAT, actividad="sostenimiento"))


def test_nivel_ordinal_acepta_romanos_palabras_y_digitos():
    assert [nivel_ordinal(x) for x in ("I", "iv", "VI", "Alto", "4", None, "???")] == [1, 4, 6, 4, 4, 0, 0]
