"""
risk_engine.py — Filtro de risco sobre sinais gerados

F007: Bloqueia sinais com confidence < 0.62
F008: Bloqueia sinais com action='hold' independente de confidence
"""
from __future__ import annotations

CONFIDENCE_THRESHOLD = 0.62


def apply_risk_filter(signal: dict) -> dict:
    """
    Aplica filtros de risco a um sinal.

    Retorna o sinal enriquecido com:
      - risk_allowed: bool
      - risk_reason: str
    """
    action = signal.get("action", "hold")
    confidence = signal.get("confidence", 0.0)

    if action == "hold":
        return {**signal, "risk_allowed": False, "risk_reason": "action_is_hold"}

    if confidence < CONFIDENCE_THRESHOLD:
        return {**signal, "risk_allowed": False, "risk_reason": "blocked_by_thresholds"}

    return {**signal, "risk_allowed": True, "risk_reason": "approved"}


def filter_signals(signals: list[dict]) -> list[dict]:
    """Aplica risk filter a todos os sinais."""
    return [apply_risk_filter(s) for s in signals]
