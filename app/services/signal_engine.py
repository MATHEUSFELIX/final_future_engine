"""
signal_engine.py — Signal generation for Future Engine.

Current implementation uses math-based mock signals (B004 — known issue).
Real implementation would use OHLCV data + technical indicators.
"""
from __future__ import annotations
import math
import hashlib
import time


# Known mock prices for common symbols
_MOCK_PRICES: dict[str, float] = {
    "BTCUSDT": 85000.0,
    "ETHUSDT": 3200.0,
    "SOLUSDT": 180.0,
    "BNBUSDT": 420.0,
    "ADAUSDT": 0.45,
}

_TIMEFRAME_MULTIPLIERS: dict[str, float] = {
    "1m": 0.1,
    "5m": 0.3,
    "15m": 0.5,
    "1h": 0.7,
    "4h": 1.0,
    "1d": 1.3,
}


def _seed_for(symbol: str, timeframe: str) -> float:
    """Deterministic seed from symbol+timeframe+hour for stable signals per window."""
    hour_bucket = int(time.time() // 3600)
    raw = f"{symbol}:{timeframe}:{hour_bucket}"
    digest = int(hashlib.md5(raw.encode()).hexdigest(), 16)
    return (digest % 10000) / 10000.0


def generate_signals(symbols: list[str], timeframe: str = "4h") -> list[dict]:
    """
    Generate trading signals for the given symbols.

    Returns signals sorted by confidence descending (F005).
    Unknown symbols default to price=100.0 (F006).
    """
    tf_mult = _TIMEFRAME_MULTIPLIERS.get(timeframe, 1.0)
    results = []

    for symbol in symbols:
        price = _MOCK_PRICES.get(symbol, 100.0)
        seed = _seed_for(symbol, timeframe)

        # Deterministic but varied signal per symbol/timeframe/hour
        angle = seed * 2 * math.pi * tf_mult
        raw_prob_up = (math.sin(angle) + 1.0) / 2.0  # 0..1

        # Clamp to reasonable range
        prob_up = round(max(0.30, min(0.70, raw_prob_up)), 4)
        prob_down = round(1.0 - prob_up, 4)

        confidence_raw = abs(prob_up - 0.5) * 2 * tf_mult
        confidence = round(min(0.99, max(0.40, confidence_raw + seed * 0.3)), 4)

        if prob_up > 0.52:
            action = "buy"
            expected_move = round((prob_up - 0.5) * price * 0.04, 4)
        elif prob_down > 0.52:
            action = "sell"
            expected_move = round(-(prob_down - 0.5) * price * 0.04, 4)
        else:
            action = "hold"
            expected_move = 0.0

        results.append({
            "symbol": symbol,
            "price": price,
            "prob_up": prob_up,
            "prob_down": prob_down,
            "confidence": confidence,
            "action": action,
            "expected_move": expected_move,
            "timeframe": timeframe,
        })

    # Sort by confidence descending (F005)
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results
