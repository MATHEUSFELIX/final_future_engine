from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    exchange_mode: str = "paper"
    exchange_provider: str = "paper"
    live_trading_enabled: bool = False
    ccxt_enabled: bool = False
    binance_api_key: str = ""
    binance_api_secret: str = ""


settings = Settings()
