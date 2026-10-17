"""Configuración desde variables de entorno (`.env` en la raíz o en `backend/`)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

RAIZ_REPO = Path(__file__).resolve().parents[2]

load_dotenv(RAIZ_REPO / ".env")
load_dotenv(RAIZ_REPO / "backend" / ".env")


def _lista(valor: str) -> list[str]:
    return [v.strip() for v in valor.split(",") if v.strip()]


@dataclass
class Settings:
    store_backend: str = field(default_factory=lambda: os.getenv("STORE_BACKEND", "memory"))
    llm_mode: str = field(default_factory=lambda: os.getenv("LLM_MODE", "fake"))
    cors_origins: list[str] = field(
        default_factory=lambda: _lista(
            os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:4173")
        )
    )
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", RAIZ_REPO / "data")))
    replays_dir: Path = field(
        default_factory=lambda: Path(os.getenv("REPLAYS_DIR", RAIZ_REPO / "replays"))
    )
    memory_dump_dir: Path | None = field(
        default_factory=lambda: Path(os.getenv("MEMORY_DUMP_DIR", RAIZ_REPO / ".memoria"))
    )
    # Factor de velocidad del replay (2.0 = el doble de rápido) y espera máxima entre eventos.
    replay_velocidad: float = field(default_factory=lambda: float(os.getenv("REPLAY_VELOCIDAD", "1.0")))
    replay_max_espera_s: float = field(
        default_factory=lambda: float(os.getenv("REPLAY_MAX_ESPERA_S", "2.0"))
    )
    run_timeout_s: float = field(default_factory=lambda: float(os.getenv("RUN_TIMEOUT_S", "120")))
