"""Tipos compartidos del módulo LLM. No dependen del contrato de datos."""
from dataclasses import dataclass, field
from typing import Any, Callable


class LLMError(Exception):
    """Error controlado del módulo LLM: el llamador decide cómo degradar."""


class LLMTimeout(LLMError):
    """El LLM no respondió dentro del tiempo límite, tras el reintento."""


class LLMRespuestaInvalida(LLMError):
    """La salida del LLM no cumple el esquema pedido, tras la corrección."""


@dataclass
class Herramienta:
    """Función que el LLM puede invocar (function calling). `funcion` puede ser sync o async."""
    nombre: str
    descripcion: str
    parametros: dict[str, Any]          # JSON Schema de los argumentos
    funcion: Callable[[dict[str, Any]], Any]


@dataclass
class UsoLLM:
    """Registro de una llamada a `completar`."""
    agente: str
    modo: str
    modelo: str
    pasos: int = 0
    intentos: int = 0
    tokens_entrada: int = 0
    tokens_salida: int = 0
    duracion_ms: int = 0
    ok: bool = True
    error: str | None = None


@dataclass
class ContextoFake:
    """Lo que recibe una respuesta fija: datos del llamador y las mismas herramientas del LLM real."""
    agente: str
    escenario_id: str | None
    contexto: dict[str, Any] = field(default_factory=dict)
    herramientas: dict[str, Herramienta] = field(default_factory=dict)

    async def llamar(self, nombre: str, **argumentos: Any) -> Any:
        """Invoca una herramienta como lo haría el LLM (para que se emitan las mismas trazas)."""
        resultado = self.herramientas[nombre].funcion(argumentos)
        if hasattr(resultado, "__await__"):
            resultado = await resultado
        return resultado
