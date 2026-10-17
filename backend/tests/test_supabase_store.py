import asyncio
import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest
from fake_supabase import FakeSupabase

from app.catalogo import cargar_catalogo_desde_dir
from app.contract import DecisionHumana, EstadoRun, EstadoSistema, Evento, Plan, Run, Tarea, TipoEvento, TurnoRef
from app.store.supabase_store import SupabaseStore, filas_catalogo

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "scripts" / "cargar_seeds.py"


def nuevo(bd=None, **kw):
    return SupabaseStore(cliente=bd or FakeSupabase(), **kw)


def run_de_prueba() -> Run:
    return Run(tarea=Tarea(tipo_tarea="TT-SOST", turno=TurnoRef(fecha=date(2026, 10, 20), turno="dia")), escenario_id="E1")


def evento(run_id, seq):
    return Evento(run_id=run_id, seq=seq, tipo=TipoEvento.RUN_ERROR, actor="sistema", payload={"mensaje": f"m{seq}"})


# -- se escribe lo que corresponde -------------------------------------------------------------------

async def test_cada_operacion_deja_su_fila_en_supabase():
    bd, store = FakeSupabase(), None
    store = nuevo(bd)
    run = run_de_prueba()
    await store.crear_run(run)
    for seq in (1, 2, 3):
        await store.agregar_evento(evento(run.id, seq))
    plan = Plan(run_id=run.id, estado_sistema=EstadoSistema.RECOMENDADO)
    await store.guardar_plan(plan)
    await store.guardar_decision(run.id, DecisionHumana(plan_id=plan.id, decision="rechazar", comentario="sin equipo", usuario="ana"))

    fila_run = bd.tablas["runs"][0]
    assert (fila_run["id"], fila_run["estado"], fila_run["modo"], fila_run["escenario_id"]) == (run.id, "EVALUANDO", "vivo", "E1")
    assert fila_run["data"]["tarea"]["tipo_tarea"] == "TT-SOST" and fila_run["tarea"]["tipo_tarea"] == "TT-SOST"
    assert [(e["seq"], e["tipo"], e["actor"]) for e in bd.tablas["eventos"]] == [(n, "run.error", "sistema") for n in (1, 2, 3)]
    assert (bd.tablas["planes"][0]["id"], bd.tablas["planes"][0]["estado_sistema"]) == (plan.id, "RECOMENDADO")
    d = bd.tablas["decisiones"][0]
    assert (d["run_id"], d["decision"], d["comentario"], d["usuario"]) == (run.id, "rechazar", "sin equipo", "ana")


async def test_los_eventos_son_idempotentes_e_inmutables():
    bd = FakeSupabase()
    store = nuevo(bd)
    run = run_de_prueba()
    await store.crear_run(run)
    await store.agregar_evento(evento(run.id, 1))
    await store.agregar_evento(Evento(run_id=run.id, seq=1, tipo=TipoEvento.RUN_ERROR, actor="sistema", payload={"mensaje": "OTRO"}))
    assert len(bd.tablas["eventos"]) == 1
    assert bd.tablas["eventos"][0]["payload"] == {"mensaje": "m1"}  # el reintento no modifica el original


async def test_un_run_se_puede_consultar_tras_reiniciar_el_backend():
    bd = FakeSupabase()
    antes = nuevo(bd)
    run = run_de_prueba()
    await antes.crear_run(run)
    run.estado = EstadoRun.APROBADA
    run.plan = Plan(run_id=run.id, estado_sistema=EstadoSistema.RECOMENDADO)
    run.decision = DecisionHumana(plan_id=run.plan.id, decision="aprobar")
    await antes.actualizar_run(run)
    await antes.agregar_evento(evento(run.id, 1))

    despues = nuevo(bd)  # instancia nueva: sin memoria del proceso anterior
    leido = await despues.leer_run(run.id)
    assert leido.estado == EstadoRun.APROBADA and leido.plan.id == run.plan.id and leido.decision.decision == "aprobar"
    assert [e.seq for e in await despues.listar_eventos(run.id)] == [1]
    assert await despues.leer_run("no-existe") is None


# -- degradación (anexo 90, regla 7) -----------------------------------------------------------------------

async def test_si_supabase_falla_el_run_continua_en_memoria():
    bd = FakeSupabase()
    bd.fallo = ConnectionError("sin red")
    store = nuevo(bd)
    run = run_de_prueba()
    await store.crear_run(run)                      # no lanza
    assert store.degradado is True
    llamadas = bd.llamadas
    for seq in (1, 2):
        await store.agregar_evento(evento(run.id, seq))
    assert [e.seq for e in await store.listar_eventos(run.id)] == [1, 2]
    assert (await store.leer_run(run.id)).id == run.id
    assert bd.llamadas == llamadas                  # degradado: ya no insiste con Supabase


async def test_una_respuesta_lenta_tambien_degrada():
    bd = FakeSupabase()
    bd.demora_s = 1.0
    store = nuevo(bd, timeout_s=0.05)
    run = run_de_prueba()
    await store.crear_run(run)
    assert store.degradado is True and (await store.leer_run(run.id)).id == run.id


# -- catálogo ------------------------------------------------------------------------------------------------

DATA = RAIZ / "data"


async def test_el_catalogo_se_lee_de_supabase_cuando_hay_seeds_cargados():
    catalogo = cargar_catalogo_desde_dir(DATA)
    bd = FakeSupabase()
    for tabla, filas in filas_catalogo(catalogo).items():
        bd.tablas[tabla] = filas
    for lista in bd.tablas.values():
        lista.reverse()  # la base no garantiza el orden de inserción: se recupera con `orden`
    leido = await nuevo(bd, data_dir=None).cargar_catalogo()   # data_dir=None: si usara archivos sería el de juguete
    assert leido == catalogo
    assert [e.id for e in leido.equipos].index("EQ-JUM-02") < [e.id for e in leido.equipos].index("EQ-JEM-01")


async def test_sin_seeds_en_supabase_se_usan_los_archivos_de_data():
    leido = await nuevo(FakeSupabase(), data_dir=DATA).cargar_catalogo()
    assert [e.id for e in leido.escenarios] == ["E1", "E2", "E2c", "E3"]


def test_filas_del_catalogo_tienen_id_columnas_y_datos():
    filas = filas_catalogo(cargar_catalogo_desde_dir(DATA))
    assert set(filas) == {"peligros", "tipos_tarea", "controles", "personas", "equipos", "incidentes", "escenarios"}
    for tabla, lista in filas.items():
        assert lista and len({f["id"] for f in lista}) == len(lista)
        assert all(f["data"]["id"] == f["id"] for f in lista)
        json.dumps(lista)  # JSON puro
    for lista in filas.values():
        assert [f["orden"] for f in lista] == list(range(len(lista)))   # la posición del archivo
    assert {"peligro_id", "bloqueante"} <= set(filas["controles"][0])
    assert "tipo_equipo" in filas["equipos"][0] and "tipo_tarea" in filas["incidentes"][0]


# -- credenciales ---------------------------------------------------------------------------------------------

def test_sin_credenciales_desde_entorno_falla_y_el_backend_cae_a_memoria(monkeypatch):
    # Vacías (no borradas): python-dotenv no pisa variables ya definidas, así que el .env de quien corre las
    # pruebas (con credenciales reales) no afecta el resultado.
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "")
    with pytest.raises(RuntimeError, match="SUPABASE_URL"):
        SupabaseStore.desde_entorno()

    from app.config import Settings
    from app.main import crear_store
    s = Settings()
    s.store_backend = "supabase"
    assert crear_store(s).nombre == "memory"


# -- cargador de seeds ---------------------------------------------------------------------------------------------

def cargar_script():
    spec = importlib.util.spec_from_file_location("cargar_seeds_script", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_cargador_valida_en_seco_los_datos_reales(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["cargar_seeds", "--data-dir", str(DATA), "--dry-run"])
    assert cargar_script().main() == 0
    assert "56 incidentes" in capsys.readouterr().out


def test_cargador_aborta_con_un_json_invalido_y_no_carga_nada(monkeypatch, tmp_path, capsys):
    for archivo in DATA.glob("*.json"):
        (tmp_path / archivo.name).write_text(archivo.read_text(encoding="utf-8"), encoding="utf-8")
    controles = json.loads((tmp_path / "controles.json").read_text(encoding="utf-8"))
    controles[0]["peligro_id"] = "PEL-INEXISTENTE"
    (tmp_path / "controles.json").write_text(json.dumps(controles), encoding="utf-8")

    cargado = []
    modulo = cargar_script()
    monkeypatch.setattr(modulo, "cargar", lambda catalogo: cargado.append(catalogo))
    monkeypatch.setattr("sys.argv", ["cargar_seeds", "--data-dir", str(tmp_path)])
    assert modulo.main() == 2 and cargado == []
    assert "PEL-INEXISTENTE" in capsys.readouterr().err


def test_cargador_es_idempotente(monkeypatch):
    bd = FakeSupabase()

    class Cliente:
        async def __call__(self, url, clave):
            return bd

    monkeypatch.setenv("SUPABASE_URL", "http://fake")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "clave-falsa")
    import supabase
    monkeypatch.setattr(supabase, "acreate_client", Cliente())
    modulo = cargar_script()
    catalogo = modulo.validar(DATA)
    asyncio.run(modulo.cargar(catalogo))
    primero = {t: len(f) for t, f in bd.tablas.items()}
    asyncio.run(modulo.cargar(catalogo))
    assert {t: len(f) for t, f in bd.tablas.items()} == primero == {
        "peligros": 4, "tipos_tarea": 4, "controles": 10, "personas": 16, "equipos": 11, "incidentes": 56, "escenarios": 4}


# -- migración -------------------------------------------------------------------------------------------------------

def test_la_migracion_activa_rls_en_todas_las_tablas_y_no_crea_politicas():
    sql = (RAIZ / "supabase" / "migrations" / "0001_init.sql").read_text(encoding="utf-8")
    import re
    tablas = re.findall(r"create table if not exists (\w+)", sql)
    con_rls = re.findall(r"alter table (\w+)\s+enable row level security", sql)
    assert len(tablas) == 12 and sorted(tablas) == sorted(con_rls)
    assert "create policy" not in sql.lower()
    assert "eventos" in tablas and "primary key (run_id, seq)" in sql
