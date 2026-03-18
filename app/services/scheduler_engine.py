"""
scheduler_engine.py — Full trading cycle orchestration.

F017: runs complete cycle (signals → risk → execution → portfolio update)
F018: returns executed=0 when all signals are blocked
F020: emits one event per processed order
"""
from __future__ import annotations
from app.services.signal_engine import generate_signals
from app.services.risk_engine import evaluate_signals
from app.services.execution_engine import execute_order
from app.services.portfolio_engine import update_position
from app.services.store import STORE
from app.core.config import settings


def run_cycle(symbols: list[str], timeframe: str = "4h") -> dict:
    """
    Execute a full trading cycle:
    1. Generate signals
    2. Filter through risk engine
    3. Execute approved orders
    4. Update portfolio positions
    5. Log events

    Returns summary with signals, orders, executed count.
    """
    # Step 1: Generate signals
    signals = generate_signals(symbols, timeframe)

    # Step 2: Risk evaluation
    evaluated = evaluate_signals(signals)

    # Cache signals
    STORE.signals = evaluated

    orders = []
    executed_count = 0

    # Step 3 & 4: Execute approved signals
    for sig in evaluated:
        if not sig.get("risk_allowed", False):
            continue

        qty_fraction = settings.default_qty_fraction
        quantity = round(qty_fraction, 8)

        order = execute_order(
            symbol=sig["symbol"],
            side=sig["action"],
            quantity=quantity,
            price=sig["price"],
            reason=f"autotrade:{sig['action']}:confidence={sig['confidence']}",
        )

        # Only record non-rejected orders
        if order["status"] != "rejected":
            STORE.append_order(order)
            orders.append(order)

            # Step 4: Update portfolio for executed orders
            update_position(order)

            # Step 5: Log event (F020)
            STORE.append_event({
                "type": "order_processed",
                "symbol": order["symbol"],
                "status": order["status"],
            })

            if order["status"] in {"executed", "submitted", "simulated"}:
                executed_count += 1

    return {
        "signals": evaluated,
        "orders": orders,
        "executed": executed_count,
        "total_signals": len(evaluated),
        "approved_signals": sum(1 for s in evaluated if s.get("risk_allowed")),
    }
