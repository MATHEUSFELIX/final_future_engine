"""
execution_engine.py — Roteador de ordens com validação integrada

O harness garante que erros são capturados ANTES de propagar.
Inspirado no linter integrado do SWE-agent: feedback no momento da ação,
não três passos depois.

Melhorias:
- Guard de quantity <= 0 antes de qualquer processamento (F013)
- Reason explícito em toda ordem bloqueada
- Validação de provider antes de tentar executar
- Response sempre tem campo 'validation_errors' para feedback do agente
"""
from __future__ import annotations
from app.core.config import settings


_VALID_SIDES = {"buy", "sell"}
_VALID_PROVIDERS = {"paper", "live_stub", "ccxt_binance"}


def _validate_order(
    symbol: str,
    side: str,
    quantity: float,
    price: float,
) -> list[str]:
    """
    Valida os parâmetros da ordem antes de qualquer tentativa de execução.
    Retorna lista de erros (vazia = válido).

    Equivalente ao linter do SWE-agent: captura erros no ponto de origem.
    """
    errors = []

    if not symbol or not isinstance(symbol, str):
        errors.append("symbol inválido ou ausente")

    if side not in _VALID_SIDES:
        errors.append(f"side='{side}' inválido. Use: {_VALID_SIDES}")

    if quantity <= 0:
        errors.append(f"quantity={quantity} inválida. Deve ser > 0")

    if price <= 0:
        errors.append(f"price={price} inválido. Deve ser > 0")

    return errors


def execute_order(
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    reason: str,
) -> dict:
    """
    Processa uma ordem através do roteador paper/live.

    O fluxo de validação é em cascata:
    1. Validação estrutural (quantity, side, etc.)
    2. Guardrail de live trading
    3. Validação de credenciais do provider
    4. Execução
    """
    mode = settings.exchange_mode
    provider = settings.exchange_provider

    # --- Camada 1: Validação estrutural ---
    validation_errors = _validate_order(symbol, side, quantity, price)
    if validation_errors:
        return {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "mode": mode,
            "status": "rejected",
            "price": price,
            "reason": f"validation_failed: {'; '.join(validation_errors)}",
            "provider": provider,
            "validation_errors": validation_errors,
        }

    # --- Camada 2: Guardrail de live trading (F012) ---
    if mode == "live" and not settings.live_trading_enabled:
        return {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "mode": mode,
            "status": "blocked",
            "price": price,
            "reason": "LIVE_TRADING_ENABLED=false — altere o .env para liberar modo real",
            "provider": provider,
            "validation_errors": [],
        }

    # --- Camada 3: Validação de credenciais para ccxt_binance ---
    if provider == "ccxt_binance":
        missing_creds = []
        if not settings.ccxt_enabled:
            missing_creds.append("CCXT_ENABLED=false")
        if not settings.binance_api_key:
            missing_creds.append("BINANCE_API_KEY ausente")
        if not settings.binance_api_secret:
            missing_creds.append("BINANCE_API_SECRET ausente")

        if missing_creds:
            return {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "mode": mode,
                "status": "simulated",
                "price": price,
                "reason": f"ccxt_binance sem credenciais completas: {', '.join(missing_creds)}",
                "provider": provider,
                "validation_errors": [],
            }

    # --- Camada 4: Execução ---
    status = "executed" if mode == "paper" else "submitted"

    return {
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "mode": mode,
        "status": status,
        "price": price,
        "reason": reason,
        "provider": provider,
        "validation_errors": [],
    }
