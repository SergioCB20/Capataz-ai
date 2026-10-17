"""Interfaz de persistencia. El dominio depende solo de esto (RF-F0-06)."""

from __future__ import annotations

from typing import Protocol

from app.contract import Catalogo, DecisionHumana, Evento, Plan, Run


class Store(Protocol):
    nombre: str  # "memory" | "supabase"; se informa en /api/health

    async def cargar_catalogo(self) -> Catalogo: ...

    async def crear_run(self, run: Run) -> None: ...

    async def leer_run(self, run_id: str) -> Run | None: ...

    async def actualizar_run(self, run: Run) -> None: ...

    async def agregar_evento(self, evento: Evento) -> None:
        """Idempotente por (run_id, seq): reintentar no duplica."""
        ...

    async def listar_eventos(self, run_id: str, desde_seq: int = 0) -> list[Evento]:
        """Eventos con `seq > desde_seq`, en orden."""
        ...

    async def guardar_plan(self, plan: Plan) -> None: ...

    async def guardar_decision(self, run_id: str, decision: DecisionHumana) -> None: ...
