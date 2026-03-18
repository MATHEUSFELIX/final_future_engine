"""
config.py — Centralized settings via environment variables.
"""
from __future__ import annotations
import os


class _Settings:
    @property
    def exchange_mode(self) -> str:
        return os.getenv("EXCHANGE_MODE", "paper").lower()

    @property
    def exchange_provider(self) -> str:
        return os.getenv("EXCHANGE_PROVIDER", "paper").lower()

    @property
    def live_trading_enabled(self) -> bool:
        return os.getenv("LIVE_TRADING_ENABLED", "false").lower() == "true"

    @property
    def ccxt_enabled(self) -> bool:
        return os.getenv("CCXT_ENABLED", "false").lower() == "true"

    @property
    def binance_api_key(self) -> str:
        return os.getenv("BINANCE_API_KEY", "")

    @property
    def binance_api_secret(self) -> str:
        return os.getenv("BINANCE_API_SECRET", "")

    @property
    def app_env(self) -> str:
        return os.getenv("APP_ENV", "dev")

    @property
    def min_confidence(self) -> float:
        return float(os.getenv("MIN_CONFIDENCE", "0.62"))

    @property
    def max_positions(self) -> int:
        return int(os.getenv("MAX_POSITIONS", "10"))

    @property
    def default_qty_fraction(self) -> float:
        return float(os.getenv("DEFAULT_QTY_FRACTION", "0.01"))


settings = _Settings()
