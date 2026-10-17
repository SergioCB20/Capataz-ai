"""Reproducción de runs grabados en `replays/<escenario_id>.json` (RF-F3-02).

El archivo es un arreglo de `Evento` (mismo formato que el SSE). Se reproduce
hasta el siguiente punto en que espera a una persona; las acciones humanas
(confirmación de campo, decisión) las aporta el usuario real, no el archivo.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.contract import Emitir, Evento, Tarea, TipoEvento

# Eventos que en el replay produce el usuario en vivo, no el archivo.
EVENTOS_HUMANOS = frozenset(
    {
        TipoEvento.HUMANO_CAMPO_CONFIRMADO,
        TipoEvento.HUMANO_DECISION_TOMADA,
        TipoEvento.RUN_FINALIZADO,
    }
)
EVENTOS_PAUSA = frozenset({TipoEvento.HUMANO_CAMPO_REQUERIDO, TipoEvento.HUMANO_DECISION_REQUERIDA})


def cargar_replay(replays_dir: Path, escenario_id: str) -> list[Evento] | None:
    ruta = replays_dir / f"{escenario_id}.json"
    if not ruta.exists():
        ruta = replays_dir / f"{escenario_id.lower()}.json"
        if not ruta.exists():
            return None
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return [Evento.model_validate(d) for d in datos]


class ReplayPlayer:
    def __init__(
        self, eventos: list[Evento], emitir: Emitir, velocidad: float = 1.0, max_espera_s: float = 2.0
    ) -> None:
        self._eventos = sorted(eventos, key=lambda e: e.seq)
        self._emitir = emitir
        self._velocidad = max(velocidad, 0.01)
        self._max_espera = max_espera_s
        self._pos = 0
        self._lock = asyncio.Lock()

    @staticmethod
    def tarea_de(eventos: list[Evento]) -> Tarea | None:
        inicio = next((e for e in eventos if e.tipo == TipoEvento.RUN_INICIADO), None)
        return Tarea.model_validate(inicio.payload["tarea"]) if inicio else None

    async def reproducir(self) -> None:
        """Emite eventos hasta la próxima pausa humana o hasta el final del archivo."""
        async with self._lock:
            previo = None
            while self._pos < len(self._eventos):
                ev = self._eventos[self._pos]
                self._pos += 1
                if ev.tipo in EVENTOS_HUMANOS:
                    continue
                if previo is not None:
                    espera = (ev.ts - previo.ts).total_seconds() / self._velocidad
                    await asyncio.sleep(min(max(espera, 0.0), self._max_espera))
                previo = ev
                await self._emitir(ev.tipo, ev.actor, ev.payload)
                if ev.tipo in EVENTOS_PAUSA or ev.tipo == TipoEvento.RUN_ERROR:
                    return
