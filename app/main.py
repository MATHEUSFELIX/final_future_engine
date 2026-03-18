from fastapi import FastAPI
from app.routers import health, signals, autotrade, ops, portfolio, backtest, scheduler

app = FastAPI(title="Future Engine", version="1.0.0")

app.include_router(health.router)
app.include_router(signals.router)
app.include_router(autotrade.router)
app.include_router(ops.router)
app.include_router(portfolio.router)
app.include_router(backtest.router)
app.include_router(scheduler.router)
