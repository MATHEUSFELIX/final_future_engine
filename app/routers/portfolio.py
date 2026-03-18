from fastapi import APIRouter
from app.services.portfolio_engine import get_positions, get_pnl

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/positions")
def positions():
    return {"positions": get_positions()}


@router.get("/pnl")
def pnl():
    return get_pnl()
