from fastapi import APIRouter
from pydantic import BaseModel
from app.services.signal_engine import generate_signals
from app.services.risk_engine import filter_signals
from app.services.execution_engine import execute_order
from app.services.portfolio_engine import update_position
from app.services.store import STORE

router = APIRouter(prefix="/autotrade", tags=["autotrade"])


class AutotradeRequest(BaseModel):
    symbols: list[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    timeframe: str = "4h"
    qty_fraction: float = 0.01


@router.post("/run")
def run_autotrade(req: AutotradeRequest):
    signals = generate_signals(req.symbols, req.timeframe)
    evaluated = filter_signals(signals)
    STORE.signals = signals

    orders = []
    for sig in evaluated:
        if not sig["risk_allowed"]:
            continue

        quantity = req.qty_fraction
        if quantity <= 0:
            continue

        order = execute_order(
            symbol=sig["symbol"],
            side=sig["action"],
            quantity=quantity,
            price=sig["price"],
            reason=f"signal:{sig['action']}:conf={sig['confidence']}",
        )

        STORE.append_order(order)
        STORE.append_event({
            "type": "order",
            "symbol": sig["symbol"],
            "status": order["status"],
        })
        update_position(order)
        orders.append(order)

    return {
        "evaluated_signals": evaluated,
        "orders": orders,
        "executed": len([o for o in orders if o["status"] in {"executed", "submitted", "simulated"}]),
    }
