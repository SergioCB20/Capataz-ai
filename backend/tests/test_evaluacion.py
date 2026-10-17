import asyncio
import importlib.util
import json
from pathlib import Path

from p3_datos import FIXTURES, casos_p3, catalogo_p3

from app.contract import EstadoSistema
from app.evaluacion import ENCABEZADO, evaluar, formatear_tabla

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "evaluar.py"


def reporte(casos=None):
    return asyncio.run(evaluar(catalogo_p3(), casos if casos is not None else casos_p3()))


def con(caso_id, **cambios):
    caso = next(c for c in casos_p3() if c.id == caso_id)
    return caso.model_copy(update=cambios)


def test_reporte_con_los_casos_de_prueba():
    r = reporte()["resumen"]
    assert (r["casos"], r["con_falla_inyectada"], r["limpios"]) == (10, 8, 2)
    assert (r["detectadas"], r["tasa_deteccion"]) == (8, 1.0)
    assert (r["detectadas_por_checklist_base"], r["detectadas_por_incidentes"], r["no_detectadas"]) == (6, 2, 0)
    assert (r["falsos_positivos"], r["tasa_falsos_positivos"], r["coinciden_con_lo_declarado"]) == (0, 0.0, 8)


def test_el_reporte_es_reproducible():
    assert reporte() == reporte()
    assert json.dumps(reporte(), sort_keys=True) == json.dumps(reporte(), sort_keys=True)


def test_el_encabezado_dice_que_los_datos_son_simulados():
    r = reporte()
    assert r["encabezado"] == ENCABEZADO and "SIMULADOS" in r["encabezado"] and "accidentes reales" in r["encabezado"]
    assert formatear_tabla(r).startswith("DATOS SIMULADOS")


def test_separa_lo_detectado_por_checklist_de_lo_detectado_por_incidentes():
    por_id = {f["id"]: f for f in reporte()["casos"]}
    assert por_id["CE-02"]["resultado"] == "checklist"
    assert (por_id["CE-07"]["resultado"], por_id["CE-07"]["primera_pasada_checklist_base"],
            por_id["CE-07"]["primera_pasada_completa"]) == ("incidentes", "RECOMENDADO", "BLOQUEADO")
    assert por_id["CE-07"]["controles_con_fallo"] == ["CTL-ARNES"]


def test_cuenta_las_fallas_por_tipo():
    tipos = reporte()["por_tipo_de_falla"]
    assert tipos["control_adicional_por_incidentes"] == {"casos": 2, "detectadas": 2, "por_checklist": 0, "por_incidentes": 2}
    assert tipos["certificacion_vencida"]["por_checklist"] == 1
    assert list(tipos) == sorted(tipos)


def test_un_caso_limpio_que_sale_distinto_es_un_falso_positivo():
    # PER-2 tiene la certificación vencida: el sistema lo bloquea, pero el caso dice que debía recomendarse.
    caso = con("CE-02", falla_inyectada=None, detectable_por=None, resultado_esperado=EstadoSistema.RECOMENDADO)
    r = reporte([caso])
    assert r["casos"][0]["resultado"] == "falso_positivo"
    assert (r["resumen"]["falsos_positivos"], r["resumen"]["tasa_falsos_positivos"]) == (1, 1.0)


def test_una_falla_que_el_sistema_no_ve_cuenta_como_no_detectada():
    # Se declara una falla inyectada, pero los datos son correctos: el sistema recomienda.
    caso = con("CE-01", falla_inyectada="falla_invisible", detectable_por="checklist", resultado_esperado=EstadoSistema.BLOQUEADO)
    r = reporte([caso])
    assert r["casos"][0]["resultado"] == "no_detectada"
    assert (r["resumen"]["detectadas"], r["resumen"]["tasa_deteccion"], r["resumen"]["no_detectadas"]) == (0, 0.0, 1)


def test_senala_cuando_lo_declarado_no_coincide_con_lo_observado():
    caso = con("CE-07", detectable_por="checklist")  # en realidad solo lo detectan los incidentes
    r = reporte([caso])
    assert r["casos"][0]["coincide_con_lo_declarado"] is False and r["resumen"]["coinciden_con_lo_declarado"] == 0


def test_sin_casos_el_reporte_no_divide_por_cero():
    assert reporte([])["resumen"]["tasa_deteccion"] is None
    assert "n/d" in formatear_tabla(reporte([]))


def cargar_script():
    spec = importlib.util.spec_from_file_location("evaluar_script", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_script_imprime_la_tabla_y_guarda_el_json(monkeypatch, tmp_path, capsys):
    salida = tmp_path / "r" / "evaluacion.json"
    monkeypatch.setattr("sys.argv", ["evaluar", "--data-dir", str(FIXTURES / "catalogo_p3"),
                                     "--casos", str(FIXTURES / "evaluacion_p3.json"), "--json", str(salida)])
    assert cargar_script().main() == 0
    assert "DATOS SIMULADOS" in capsys.readouterr().out
    guardado = json.loads(salida.read_text(encoding="utf-8"))
    assert guardado["resumen"]["casos"] == 10 and guardado == json.loads(json.dumps(reporte()))

    # dos ejecuciones seguidas dejan el mismo archivo
    primero = salida.read_text(encoding="utf-8")
    cargar_script().main()
    assert salida.read_text(encoding="utf-8") == primero


def test_script_sin_archivo_de_casos_falla_con_mensaje_claro(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("sys.argv", ["evaluar", "--data-dir", str(tmp_path / "vacio"), "--sin-json"])
    assert cargar_script().main() == 2
    assert "evaluacion.json" in capsys.readouterr().err


def test_script_con_un_caso_invalido_falla_con_mensaje_claro(monkeypatch, tmp_path, capsys):
    malo = tmp_path / "casos.json"
    malo.write_text(json.dumps([{"id": "X"}]), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["evaluar", "--data-dir", str(FIXTURES / "catalogo_p3"), "--casos", str(malo), "--sin-json"])
    assert cargar_script().main() == 2
    assert "inválidos" in capsys.readouterr().err
