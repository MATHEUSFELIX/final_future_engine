from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "env": {
            "exchange_mode": settings.exchange_mode,
            "exchange_provider": settings.exchange_provider,
            "live_trading_enabled": settings.live_trading_enabled,
        },
    }
