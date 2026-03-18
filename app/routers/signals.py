from fastapi import APIRouter
from pydantic import BaseModel
from app.services.signal_engine import generate_signals
from app.services.store import STORE

router = APIRouter(prefix="/signals", tags=["signals"])


class SignalRequest(BaseModel):
    symbols: list[str]
    timeframe: str = "4h"


@router.post("/generate")
def generate(req: SignalRequest):
    signals = generate_signals(req.symbols, req.timeframe)
    STORE.signals = signals
    return {"signals": signals}
