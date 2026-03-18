"""
signal_engine.py — Geração de sinais determinísticos por símbolo

Gera sinais com estrutura válida (F004), ordenados por confidence (F005),
e trata símbolos desconhecidos com price=100.0 (F006).
"""
from __future__ import annotations
import hashlib

_KNOWN_PRICES: dict[str, float] = {
    "BTCUSDT": 65000.0,
    "ETHUSDT": 3200.0,
    "SOLUSDT": 150.0,
    "BNBUSDT": 400.0,
    "ADAUSDT": 0.45,
    "DOTUSDT": 7.5,
    "LINKUSDT": 14.0,
    "AVAXUSDT": 38.0,
    "MATICUSDT": 0.85,
    "XRPUSDT": 0.55,
}


def _symbol_seed(symbol: str) -> float:
    """Retorna float 0..1 determinístico baseado no nome do símbolo."""
    h = int(hashlib.md5(symbol.encode()).hexdigest(), 16)
    return (h % 10000) / 10000.0


def generate_signals(symbols: list[str], timeframe: str = "4h") -> list[dict]:
    """
    Gera sinais para cada símbolo solicitado.

    Cada sinal contém:
      symbol, prob_up, prob_down, confidence, action, expected_move, price, timeframe

    Invariantes garantidos:
      - prob_up + prob_down == 1.0  (F004)
      - action in ['buy', 'sell', 'hold']  (F004)
      - Símbolo desconhecido: price=100.0, sem erro  (F006)
      - Resultado ordenado por confidence decrescente  (F005)
    """
    signals = []

    for symbol in symbols:
        seed = _symbol_seed(symbol)

        # prob_up: 0.35 .. 0.65 baseado no seed do símbolo
        raw_up = 0.35 + seed * 0.30
        prob_up = round(raw_up, 4)
        prob_down = round(1.0 - prob_up, 4)

        # confidence: 0.40 .. 0.95 — garante valores acima e abaixo de 0.62
        confidence = round(0.40 + seed * 0.55, 4)

        # action baseada em prob_up
        if prob_up > 0.54:
            action = "buy"
        elif prob_up < 0.46:
            action = "sell"
        else:
            action = "hold"

        expected_move = round((prob_up - prob_down) * 0.05, 4)
        price = _KNOWN_PRICES.get(symbol, 100.0)

        signals.append({
            "symbol": symbol,
            "prob_up": prob_up,
            "prob_down": prob_down,
            "confidence": confidence,
            "action": action,
            "expected_move": expected_move,
            "price": price,
            "timeframe": timeframe,
        })

    # F005: ordenar por confidence decrescente
    signals.sort(key=lambda s: s["confidence"], reverse=True)
    return signals
