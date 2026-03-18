"""
risk_engine.py — Risk filtering for signal approval.

F007: blocks signals with confidence < MIN_CONFIDENCE
F008: blocks signals with action == 'hold'
"""
from __future__ import annotations
from app.core.config import settings


def evaluate_signals(signals: list[dict]) -> list[dict]:
    """
    Evaluate each signal and annotate with risk_allowed and risk_reason.
    """
    min_confidence = settings.min_confidence
    evaluated = []

    for sig in signals:
        action = sig.get("action", "hold")
        confidence = sig.get("confidence", 0.0)

        if action == "hold":
            risk_allowed = False
            risk_reason = "action_is_hold"
        elif confidence < min_confidence:
            risk_allowed = False
            risk_reason = "blocked_by_thresholds"
        else:
            risk_allowed = True
            risk_reason = "approved"

        evaluated.append({**sig, "risk_allowed": risk_allowed, "risk_reason": risk_reason})

    return evaluated
