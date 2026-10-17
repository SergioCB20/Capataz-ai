"""Store en memoria con volcado JSONL por run (respaldo sin red, RT-08)."""

from __future__ import annotations

from pathlib import Path

from app.catalogo import cargar_catalogo_desde_dir
from app.contract import Catalogo, DecisionHumana, Evento, Plan, Run


class MemoryStore:
    nombre = "memory"

    def __init__(self, data_dir: Path | None = None, dump_dir: Path | None = None) -> None:
        self._data_dir = data_dir
        self._dump_dir = dump_dir
        self._catalogo: Catalogo | None = None
        self._runs: dict[str, Run] = {}
        self._eventos: dict[str, dict[int, Evento]] = {}
        self._planes: dict[str, Plan] = {}
        self._decisiones: dict[str, list[DecisionHumana]] = {}

    async def cargar_catalogo(self) -> Catalogo:
        if self._catalogo is None:
            self._catalogo = cargar_catalogo_desde_dir(self._data_dir)
        return self._catalogo

    async def crear_run(self, run: Run) -> None:
        self._runs[run.id] = run.model_copy(deep=True)
        self._eventos.setdefault(run.id, {})

    async def leer_run(self, run_id: str) -> Run | None:
        run = self._runs.get(run_id)
        return run.model_copy(deep=True) if run else None

    async def actualizar_run(self, run: Run) -> None:
        self._runs[run.id] = run.model_copy(deep=True)

    async def agregar_evento(self, evento: Evento) -> None:
        eventos = self._eventos.setdefault(evento.run_id, {})
        if evento.seq in eventos:
            return
        eventos[evento.seq] = evento
        self._volcar(evento)

    async def listar_eventos(self, run_id: str, desde_seq: int = 0) -> list[Evento]:
        eventos = self._eventos.get(run_id, {})
        return [eventos[s] for s in sorted(eventos) if s > desde_seq]

    async def guardar_plan(self, plan: Plan) -> None:
        self._planes[plan.id] = plan

    async def guardar_decision(self, run_id: str, decision: DecisionHumana) -> None:
        self._decisiones.setdefault(run_id, []).append(decision)

    def _volcar(self, evento: Evento) -> None:
        if self._dump_dir is None:
            return
        try:
            self._dump_dir.mkdir(parents=True, exist_ok=True)
            with open(self._dump_dir / f"{evento.run_id}.jsonl", "a", encoding="utf-8") as f:
                f.write(evento.model_dump_json() + "\n")
        except OSError:
            pass  # el volcado es una ayuda; nunca debe tumbar un run
