"""
main.py — Future Engine API

FastAPI application exposing all trading engine endpoints.
"""
from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.services.store import STORE
from app.services.signal_engine import generate_signals
from app.services.risk_engine import evaluate_signals
from app.services.execution_engine import execute_order
from app.services.portfolio_engine import update_position, get_positions, get_pnl
from app.services.backtest_engine import run_backtest
from app.services.scheduler_engine import run_cycle

app = FastAPI(title="Future Engine", version="1.0.0")


# --- Request models ---

class SignalRequest(BaseModel):
    symbols: list[str]
    timeframe: str = "4h"


class AutotradeRequest(BaseModel):
    symbols: list[str]
    timeframe: str = "4h"


class BacktestRequest(BaseModel):
    symbol: str
    periods: int = 180
    timeframe: str = "4h"


class SchedulerRequest(BaseModel):
    symbols: list[str]
    timeframe: str = "4h"


# --- Health ---

@app.get("/health")
def health():
    """F001: API health check."""
    return {"status": "ok", "env": settings.app_env}


# --- Signals ---

@app.post("/signals/generate")
def signals_generate(req: SignalRequest):
    """F004-F006: Generate trading signals."""
    signals = generate_signals(req.symbols, req.timeframe)
    STORE.signals = signals
    return {"signals": signals, "count": len(signals)}


# --- Autotrade ---

@app.post("/autotrade/run")
def autotrade_run(req: AutotradeRequest):
    """F007-F013: Run autotrade cycle with risk filtering and execution."""
    signals = generate_signals(req.symbols, req.timeframe)
    evaluated = evaluate_signals(signals)
    STORE.signals = evaluated

    orders = []
    for sig in evaluated:
        if not sig.get("risk_allowed", False):
            continue

        quantity = round(settings.default_qty_fraction, 8)
        order = execute_order(
            symbol=sig["symbol"],
            side=sig["action"],
            quantity=quantity,
            price=sig["price"],
            reason=f"autotrade:{sig['action']}:conf={sig['confidence']}",
        )

        if order["status"] != "rejected":
            STORE.append_order(order)
            update_position(order)
            STORE.append_event({
                "type": "order_processed",
                "symbol": order["symbol"],
                "status": order["status"],
            })

        orders.append(order)

    return {
        "signals": evaluated,
        "orders": orders,
        "executed": sum(1 for o in orders if o["status"] in {"executed", "submitted", "simulated"}),
    }


# --- Backtest ---

@app.post("/backtest/run")
def backtest_run(req: BacktestRequest):
    """F009-F010: Run backtest simulation."""
    result = run_backtest(req.symbol, req.periods, req.timeframe)
    return result


# --- Scheduler ---

@app.post("/scheduler/run-cycle")
def scheduler_run_cycle(req: SchedulerRequest):
    """F017-F018: Full trading cycle via scheduler."""
    result = run_cycle(req.symbols, req.timeframe)
    return result


# --- Portfolio ---

@app.get("/portfolio/positions")
def portfolio_positions():
    """F014-F015: Get current open positions."""
    return {"positions": get_positions()}


@app.get("/portfolio/pnl")
def portfolio_pnl():
    """F016: Get PnL summary."""
    return get_pnl()


# --- Ops ---

@app.get("/ops/orders")
def ops_orders():
    """F002, F011: List all orders."""
    return {"orders": STORE.orders, "count": len(STORE.orders)}


@app.get("/ops/events")
def ops_events():
    """F020: List all events."""
    return {"events": STORE.events, "count": len(STORE.events)}


@app.get("/ops/status")
def ops_status():
    """F019: System status reflecting .env configuration."""
    return {
        "exchange_mode": settings.exchange_mode,
        "exchange_provider": settings.exchange_provider,
        "live_trading_enabled": settings.live_trading_enabled,
        "ccxt_enabled": settings.ccxt_enabled,
        "app_env": settings.app_env,
        "signals": len(STORE.signals),
        "orders": len(STORE.orders),
        "events": len(STORE.events),
    }
