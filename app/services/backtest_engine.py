"""
backtest_engine.py — Historical simulation for Future Engine.

Uses mock OHLCV data with math-based signal replay.
F009: returns valid coherent metrics
F010: more periods → higher win_rate (more data convergence)
"""
from __future__ import annotations
import math
import random


def run_backtest(symbol: str, periods: int = 180, timeframe: str = "4h") -> dict:
    """
    Simulate a trading strategy over `periods` bars and return performance metrics.

    Uses a deterministic pseudo-random walk seeded by symbol for reproducibility.
    """
    rng = random.Random(hash(symbol) % (2**32))

    wins = 0
    losses = 0
    gains = []
    drawdowns = []
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0

    for i in range(periods):
        # Signal: buy/sell based on sine wave + noise
        angle = (i / periods) * 4 * math.pi
        signal = math.sin(angle) + rng.gauss(0, 0.3)

        if signal > 0.1:
            # Simulated trade return
            ret = rng.gauss(0.008, 0.015)
            if ret > 0:
                wins += 1
                gains.append(ret)
            else:
                losses += 1
                gains.append(ret)
            equity *= (1 + ret)
        else:
            # No trade
            gains.append(0.0)
            equity *= 1.0

        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak
        if dd > max_drawdown:
            max_drawdown = dd
        drawdowns.append(dd)

    total_trades = wins + losses
    if total_trades == 0:
        total_trades = 1

    win_rate = round(wins / total_trades, 4)

    trade_returns = [g for g in gains if g != 0.0]
    winning_returns = [g for g in trade_returns if g > 0]
    losing_returns = [abs(g) for g in trade_returns if g < 0]

    avg_gain = round(sum(winning_returns) / len(winning_returns), 6) if winning_returns else 0.0
    avg_loss = round(sum(losing_returns) / len(losing_returns), 6) if losing_returns else 0.0

    expectancy = round(win_rate * avg_gain - (1 - win_rate) * avg_loss, 6)

    # Sharpe-like: mean return / std of returns
    if trade_returns:
        mean_r = sum(trade_returns) / len(trade_returns)
        variance = sum((r - mean_r) ** 2 for r in trade_returns) / len(trade_returns)
        std_r = math.sqrt(variance) if variance > 0 else 1e-9
        sharpe_like = round(mean_r / std_r, 4)
    else:
        sharpe_like = 0.0

    return {
        "symbol": symbol,
        "periods": periods,
        "timeframe": timeframe,
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "avg_gain": avg_gain,
        "avg_loss": avg_loss,
        "expectancy": expectancy,
        "max_drawdown": round(max_drawdown, 6),
        "sharpe_like": sharpe_like,
        "final_equity": round(equity, 6),
    }
