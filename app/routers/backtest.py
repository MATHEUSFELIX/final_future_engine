from fastapi import APIRouter
from pydantic import BaseModel
from app.services.backtest_engine import run_backtest

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    symbol: str = "BTCUSDT"
    periods: int = 180
    timeframe: str = "4h"


@router.post("/run")
def backtest(req: BacktestRequest):
    return run_backtest(req.symbol, req.periods, req.timeframe)
