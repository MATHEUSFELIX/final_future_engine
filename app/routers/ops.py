from fastapi import APIRouter
from app.services.store import STORE
from app.core.config import settings

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/orders")
def get_orders():
    return {"orders": STORE.orders}


@router.get("/events")
def get_events():
    return {"events": STORE.events}


@router.get("/status")
def get_status():
    return {
        "exchange_mode": settings.exchange_mode,
        "live_trading_enabled": settings.live_trading_enabled,
        "exchange_provider": settings.exchange_provider,
        "ccxt_enabled": settings.ccxt_enabled,
        "signals": len(STORE.signals),
        "orders": len(STORE.orders),
        "events": len(STORE.events),
        "positions": len(STORE.positions),
    }
