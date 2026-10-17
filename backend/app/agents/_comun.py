"""Utilidades de los agentes de verificación Personal y Equipo (P3)."""
import time
from typing import Any, Callable

from app.contract import Emitir, Evidencia, Fuente, Tarea, TipoEvento, TraceHerramienta


async def llamar_herramienta(
    emitir: Emitir, actor: str, nombre: str, entrada: dict[str, Any],
    funcion: Callable[[], Any], resumir: Callable[[Any], str],
) -> Any:
    """Ejecuta una herramienta y emite `agente.herramienta` con su traza (RF-F1-15)."""
    inicio = time.perf_counter()
    resultado = funcion()
    traza = TraceHerramienta(nombre=nombre, entrada=entrada, salida_resumen=resumir(resultado),
                             duracion_ms=int((time.perf_counter() - inicio) * 1000))
    await emitir(TipoEvento.AGENTE_HERRAMIENTA, actor, {"agente": actor, "trace": traza})
    return resultado


def evidencia_de_asignacion(tarea: Tarea, campo: str, valor: list[str]) -> Evidencia:
    """Respaldo cuando el motivo es lo que la tarea tiene (o no) asignado."""
    return Evidencia(registro=f"tareas/{tarea.id}", campo=campo, valor=valor, fuente=Fuente())
