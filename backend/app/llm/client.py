"""Cliente LLM de CAPATAZ: única puerta al LLM (OpenRouter, API compatible con OpenAI).

El resto del sistema solo depende de `ClienteLLM.completar`. Los detalles del modelo
concreto (parámetros, límites, formato exacto de las llamadas a funciones) no se suponen:
el modelo sale de `LLM_MODEL`.

La salida estructurada se pide por function calling: el modelo termina llamando a la
función `responder`, cuyo esquema es el del modelo Pydantic pedido, y el resultado se
valida con Pydantic.
"""
import asyncio
import importlib.util
import inspect
import json
import logging
import os
import time
from typing import Any, Awaitable, Callable, TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.fake import buscar_fake
from app.llm.tipos import (
    ContextoFake, Herramienta, LLMError, LLMRespuestaInvalida, LLMTimeout, UsoLLM,
)

log = logging.getLogger("capataz.llm")

T = TypeVar("T", bound=BaseModel)
Api = Callable[[list[dict[str, Any]], list[dict[str, Any]]], Awaitable[Any]]

URL_OPENROUTER = "https://openrouter.ai/api/v1"
FUNCION_FINAL = "responder"


def _tool_message(msg: Any) -> dict[str, Any]:
    """Mensaje del asistente en formato de chat, a partir de la respuesta del SDK."""
    out: dict[str, Any] = {"role": "assistant", "content": getattr(msg, "content", None)}
    llamadas = getattr(msg, "tool_calls", None) or []
    if llamadas:
        out["tool_calls"] = [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in llamadas
        ]
    return out


class ClienteLLM:
    def __init__(
        self,
        modo: str = "fake",
        modelo: str | None = None,
        api_key: str | None = None,
        base_url: str = URL_OPENROUTER,
        timeout_s: float = 30.0,
        reintentos: int = 1,
        temperatura: float = 0.2,
        api: Api | None = None,
    ) -> None:
        if modo not in ("real", "fake"):
            raise ValueError(f"LLM_MODE inválido: {modo!r} (usar 'real' o 'fake')")
        self.modo = modo
        self.modelo = modelo or ("fake" if modo == "fake" else "")
        self.api_key = api_key
        self.base_url = base_url
        self.timeout_s = timeout_s
        self.reintentos = reintentos
        self.temperatura = temperatura
        self.usos: list[UsoLLM] = []
        self._openai: Any = None
        self._api: Api = api or self._api_openai
        if modo == "real" and api is None:
            if not self.modelo:
                raise LLMError("Falta LLM_MODEL para el modo real")
            if not api_key:
                raise LLMError("Falta OPENROUTER_API_KEY para el modo real")
            if importlib.util.find_spec("openai") is None:
                raise LLMError("Falta el paquete `openai` (se usa como cliente de OpenRouter)")

    @classmethod
    def desde_entorno(cls) -> "ClienteLLM":
        return cls(
            modo=os.getenv("LLM_MODE", "fake"),
            modelo=os.getenv("LLM_MODEL"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", URL_OPENROUTER),
            timeout_s=float(os.getenv("LLM_TIMEOUT_S", "30")),
            temperatura=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        )

    async def completar(
        self,
        *,
        agente: str,
        sistema: str,
        usuario: str,
        esquema: type[T],
        herramientas: list[Herramienta] | None = None,
        escenario_id: str | None = None,
        contexto_fake: dict[str, Any] | None = None,
        max_pasos: int = 6,
    ) -> T:
        """Devuelve una instancia de `esquema`. Lanza LLMError (o subclase) si no se logra."""
        uso = UsoLLM(agente=agente, modo=self.modo, modelo=self.modelo)
        inicio = time.perf_counter()
        try:
            if self.modo == "fake":
                return await self._completar_fake(
                    agente, esquema, herramientas or [], escenario_id, contexto_fake or {})
            return await self._completar_real(
                uso, sistema, usuario, esquema, herramientas or [], max_pasos)
        except Exception as e:
            uso.ok, uso.error = False, f"{type(e).__name__}: {e}"
            raise
        finally:
            uso.duracion_ms = int((time.perf_counter() - inicio) * 1000)
            self.usos.append(uso)
            log.info("llm agente=%s modo=%s ok=%s pasos=%d intentos=%d tokens=%d/%d ms=%d",
                     agente, self.modo, uso.ok, uso.pasos, uso.intentos,
                     uso.tokens_entrada, uso.tokens_salida, uso.duracion_ms)

    # -- modo fake -----------------------------------------------------------------

    async def _completar_fake(self, agente: str, esquema: type[T], herramientas: list[Herramienta],
                              escenario_id: str | None, contexto: dict[str, Any]) -> T:
        fn = buscar_fake(agente, escenario_id)
        if fn is None:
            raise LLMError(f"No hay respuesta fake para el agente {agente!r}")
        ctx = ContextoFake(agente, escenario_id, contexto, {h.nombre: h for h in herramientas})
        bruto = fn(ctx)
        if inspect.isawaitable(bruto):
            bruto = await bruto
        if isinstance(bruto, BaseModel):
            bruto = bruto.model_dump(mode="json")
        try:
            return esquema.model_validate(bruto)
        except ValidationError as e:
            raise LLMRespuestaInvalida(f"La respuesta fake de {agente!r} no cumple el esquema: {e}") from e

    # -- modo real -----------------------------------------------------------------

    async def _completar_real(self, uso: UsoLLM, sistema: str, usuario: str, esquema: type[T],
                              herramientas: list[Herramienta], max_pasos: int) -> T:
        por_nombre = {h.nombre: h for h in herramientas}
        tools = [
            {"type": "function",
             "function": {"name": h.nombre, "description": h.descripcion, "parameters": h.parametros}}
            for h in herramientas
        ] + [{
            "type": "function",
            "function": {"name": FUNCION_FINAL,
                         "description": "Entrega la respuesta final. Debe ser la última llamada.",
                         "parameters": esquema.model_json_schema()},
        }]
        mensajes: list[dict[str, Any]] = [
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ]
        correcciones, recordatorios = 1, 1

        for paso in range(1, max_pasos + 1):
            uso.pasos = paso
            msg = await self._llamar_api(uso, mensajes, tools)
            llamadas = list(getattr(msg, "tool_calls", None) or [])
            mensajes.append(_tool_message(msg))

            if not llamadas:
                if recordatorios == 0:
                    raise LLMRespuestaInvalida("El modelo no entregó la respuesta estructurada")
                recordatorios -= 1
                mensajes.append({"role": "user",
                                 "content": f"Entrega la respuesta llamando a la función `{FUNCION_FINAL}`."})
                continue

            resultado: T | None = None
            invalida = False
            for tc in llamadas:
                nombre = tc.function.name
                if nombre == FUNCION_FINAL:
                    try:
                        resultado = esquema.model_validate_json(tc.function.arguments)
                        contenido = "ok"
                    except ValidationError as e:
                        invalida = True
                        contenido = f"Respuesta inválida, corrígela y vuelve a llamar `{FUNCION_FINAL}`: {e}"
                elif nombre in por_nombre:
                    contenido = await self._ejecutar_herramienta(por_nombre[nombre], tc.function.arguments)
                else:
                    contenido = json.dumps({"error": f"herramienta desconocida: {nombre}"})
                mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": contenido})

            if resultado is not None:
                return resultado
            if invalida:
                if correcciones == 0:
                    raise LLMRespuestaInvalida("La respuesta del modelo no cumple el esquema tras la corrección")
                correcciones -= 1

        raise LLMRespuestaInvalida(f"El modelo no terminó en {max_pasos} pasos")

    async def _ejecutar_herramienta(self, herramienta: Herramienta, argumentos: str) -> str:
        """Un fallo de la herramienta se devuelve al modelo como error; no aborta la llamada."""
        try:
            args = json.loads(argumentos or "{}")
            resultado = herramienta.funcion(args)
            if inspect.isawaitable(resultado):
                resultado = await resultado
        except Exception as e:
            log.warning("herramienta %s falló: %s", herramienta.nombre, e)
            return json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False)
        return resultado if isinstance(resultado, str) else json.dumps(resultado, ensure_ascii=False, default=str)

    async def _llamar_api(self, uso: UsoLLM, mensajes: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        """Una llamada al modelo con tiempo límite y `reintentos` reintentos."""
        ultimo: LLMError | None = None
        for _ in range(self.reintentos + 1):
            uso.intentos += 1
            try:
                resp = await asyncio.wait_for(self._api(mensajes, tools), timeout=self.timeout_s)
                usage = getattr(resp, "usage", None)
                uso.tokens_entrada += getattr(usage, "prompt_tokens", 0) or 0
                uso.tokens_salida += getattr(usage, "completion_tokens", 0) or 0
                return resp.choices[0].message
            except asyncio.TimeoutError:
                ultimo = LLMTimeout(f"Sin respuesta del LLM en {self.timeout_s:g} s")
            except Exception as e:
                ultimo = LLMError(f"{type(e).__name__}: {e}")
            log.warning("llm intento %d/%d falló: %s", uso.intentos, self.reintentos + 1, ultimo)
        assert ultimo is not None
        raise ultimo

    async def _api_openai(self, mensajes: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        if self._openai is None:
            from openai import AsyncOpenAI
            self._openai = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, max_retries=0)
        return await self._openai.chat.completions.create(
            model=self.modelo, messages=mensajes, tools=tools, temperature=self.temperatura)


_cliente: ClienteLLM | None = None


def get_cliente() -> ClienteLLM:
    """Cliente global, creado desde el entorno la primera vez."""
    global _cliente
    if _cliente is None:
        _cliente = ClienteLLM.desde_entorno()
    return _cliente


def set_cliente(cliente: ClienteLLM | None) -> None:
    """Para tests y para que P1 inyecte un cliente propio."""
    global _cliente
    _cliente = cliente
