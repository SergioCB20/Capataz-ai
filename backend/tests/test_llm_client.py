import asyncio
import json
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app.llm import ClienteLLM, Herramienta, LLMError, LLMRespuestaInvalida, LLMTimeout, registrar_fake


class Saludo(BaseModel):
    texto: str


def llamada(id_: str, nombre: str, argumentos: dict | str):
    args = argumentos if isinstance(argumentos, str) else json.dumps(argumentos)
    return SimpleNamespace(id=id_, function=SimpleNamespace(name=nombre, arguments=args))


def respuesta(*tool_calls, contenido=None):
    msg = SimpleNamespace(content=contenido, tool_calls=list(tool_calls))
    return SimpleNamespace(
        choices=[SimpleNamespace(message=msg)],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )


def api_guionada(*respuestas):
    """API falsa que devuelve las respuestas en orden (una Exception se lanza) y cuenta las llamadas."""
    cola = list(respuestas)
    llamadas = []

    async def api(mensajes, tools):
        llamadas.append(list(mensajes))
        item = cola.pop(0)
        if isinstance(item, Exception):
            raise item
        if callable(item):
            return await item()
        return item

    api.llamadas = llamadas
    return api


def cliente_real(api, **kw):
    return ClienteLLM(modo="real", modelo="modelo-x", api=api, timeout_s=kw.pop("timeout_s", 1), **kw)


def completar(cliente, **kw):
    return asyncio.run(cliente.completar(agente="a", sistema="s", usuario="u", esquema=Saludo, **kw))


# -- modo fake ---------------------------------------------------------------------

def test_fake_devuelve_respuesta_fija_sin_red():
    registrar_fake("saludador", lambda ctx: {"texto": "hola"})
    c = ClienteLLM(modo="fake")
    r = asyncio.run(c.completar(agente="saludador", sistema="", usuario="", esquema=Saludo))
    assert r.texto == "hola"


def test_fake_prefiere_la_respuesta_del_escenario():
    registrar_fake("saludador2", lambda ctx: {"texto": "general"})
    registrar_fake("saludador2", lambda ctx: {"texto": "e2"}, escenario_id="E2")
    c = ClienteLLM(modo="fake")
    pedir = lambda esc: asyncio.run(c.completar(
        agente="saludador2", sistema="", usuario="", esquema=Saludo, escenario_id=esc)).texto
    assert (pedir("E2"), pedir("E1"), pedir(None)) == ("e2", "general", "general")


def test_fake_sin_respuesta_registrada_es_error_controlado():
    c = ClienteLLM(modo="fake")
    with pytest.raises(LLMError):
        asyncio.run(c.completar(agente="no-existe", sistema="", usuario="", esquema=Saludo))


def test_fake_con_salida_invalida_es_error_controlado():
    registrar_fake("roto", lambda ctx: {"otra_cosa": 1})
    with pytest.raises(LLMRespuestaInvalida):
        asyncio.run(ClienteLLM(modo="fake").completar(agente="roto", sistema="", usuario="", esquema=Saludo))


# -- modo real: respuesta estructurada, tiempo límite y reintento -------------------

def test_real_devuelve_la_respuesta_validada_y_registra_uso():
    api = api_guionada(respuesta(llamada("1", "responder", {"texto": "hola"})))
    c = cliente_real(api)
    assert completar(c).texto == "hola"
    uso = c.usos[0]
    assert (uso.ok, uso.intentos, uso.tokens_entrada, uso.tokens_salida) == (True, 1, 10, 5)


def test_real_reintenta_una_vez_tras_un_fallo():
    api = api_guionada(ConnectionError("red caída"), respuesta(llamada("1", "responder", {"texto": "ok"})))
    c = cliente_real(api)
    assert completar(c).texto == "ok"
    assert c.usos[0].intentos == 2


def test_real_tiempo_limite_reintenta_una_vez_y_lanza_error_controlado():
    async def lenta():
        await asyncio.sleep(5)

    api = api_guionada(lenta, lenta)
    c = cliente_real(api, timeout_s=0.05)
    with pytest.raises(LLMTimeout):
        completar(c)
    assert len(api.llamadas) == 2
    assert c.usos[0].ok is False


def test_real_dos_fallos_seguidos_lanzan_error_controlado():
    c = cliente_real(api_guionada(ConnectionError("a"), ConnectionError("b")))
    with pytest.raises(LLMError):
        completar(c)


# -- modo real: function calling y salida inválida ----------------------------------

def test_real_ejecuta_herramientas_y_devuelve_su_resultado_al_modelo():
    vistos = []

    async def sumar(args):
        vistos.append(args)
        return {"suma": args["a"] + args["b"]}

    herramienta = Herramienta("sumar", "suma", {"type": "object", "properties": {}}, sumar)
    api = api_guionada(
        respuesta(llamada("1", "sumar", {"a": 1, "b": 2})),
        respuesta(llamada("2", "responder", {"texto": "3"})),
    )
    c = cliente_real(api)
    assert completar(c, herramientas=[herramienta]).texto == "3"
    assert vistos == [{"a": 1, "b": 2}]
    mensaje_tool = [m for m in api.llamadas[1] if m["role"] == "tool"][0]
    assert json.loads(mensaje_tool["content"]) == {"suma": 3}


def test_real_un_fallo_de_herramienta_se_informa_al_modelo_sin_abortar():
    def rota(args):
        raise RuntimeError("boom")

    herramienta = Herramienta("rota", "x", {"type": "object", "properties": {}}, rota)
    api = api_guionada(
        respuesta(llamada("1", "rota", {})),
        respuesta(llamada("2", "responder", {"texto": "sigo"})),
    )
    assert completar(cliente_real(api), herramientas=[herramienta]).texto == "sigo"
    mensaje_tool = [m for m in api.llamadas[1] if m["role"] == "tool"][0]
    assert "boom" in mensaje_tool["content"]


def test_real_corrige_una_salida_invalida_una_vez():
    api = api_guionada(
        respuesta(llamada("1", "responder", {"mal": 1})),
        respuesta(llamada("2", "responder", {"texto": "bien"})),
    )
    assert completar(cliente_real(api)).texto == "bien"


def test_real_dos_salidas_invalidas_lanzan_error_controlado():
    api = api_guionada(
        respuesta(llamada("1", "responder", {"mal": 1})),
        respuesta(llamada("2", "responder", "no es json")),
    )
    with pytest.raises(LLMRespuestaInvalida):
        completar(cliente_real(api))


def test_real_si_el_modelo_responde_texto_se_le_pide_la_funcion_final():
    api = api_guionada(
        respuesta(contenido="hola"),
        respuesta(llamada("1", "responder", {"texto": "ya"})),
    )
    assert completar(cliente_real(api)).texto == "ya"


# -- configuración -------------------------------------------------------------------

def test_modo_real_sin_clave_o_modelo_falla_al_crear_el_cliente():
    with pytest.raises(LLMError):
        ClienteLLM(modo="real", modelo="m", api_key=None)
    with pytest.raises(LLMError):
        ClienteLLM(modo="real", modelo=None, api_key="k")


def test_modo_invalido():
    with pytest.raises(ValueError):
        ClienteLLM(modo="otro")


def test_desde_entorno_por_defecto_es_fake(monkeypatch):
    monkeypatch.delenv("LLM_MODE", raising=False)
    assert ClienteLLM.desde_entorno().modo == "fake"
