"""Único punto por el que el código de P2 importa los modelos del contrato.

Usa `app.contract` (P1) cuando existe; si no, los modelos temporales. Cuando P1 suba
el contrato, dejar solo `from app.contract import *` y borrar `_contrato_temp.py`.
"""
try:
    from app.contract import *  # noqa: F401,F403
except ImportError:
    from app.agents._contrato_temp import *  # noqa: F401,F403
