"""
portfolio_engine.py — Gestão de posições com VWAP correto

Correções aplicadas:
- F014: avg_price agora é calculado como VWAP (média ponderada pelo custo)
- F013: ordens com quantity <= 0 são ignoradas
- F015: apenas ordens com status in {executed, submitted, simulated} atualizam posição
"""
from __future__ import annotations
from app.services.store import STORE


def update_position(order: dict) -> None:
    """
    Atualiza posição do símbolo com base na ordem executada.

    Usa VWAP (Volume Weighted Average Price) para calcular avg_price:
      novo_total_cost = custo_atual + (qty * price)
      nova_qty = qty_atual + qty_signed
      novo_avg_price = novo_total_cost / abs(nova_qty)  se nova_qty != 0

    Guard: ordens com status bloqueado ou quantity <= 0 são ignoradas.
    """
    # Guard F015: só ordens efetivamente executadas
    if order["status"] not in {"executed", "submitted", "simulated"}:
        return

    # Guard F013: quantity deve ser positiva
    if order.get("quantity", 0) <= 0:
        return

    sym = order["symbol"]
    price = order["price"]
    qty = order["quantity"]
    signed_qty = qty if order["side"] == "buy" else -qty

    # Buscar posição atual do SQLiteStore
    current = STORE.get_position(sym)
    if current is None:
        current = {"symbol": sym, "net_qty": 0.0, "avg_price": 0.0, "total_cost": 0.0}

    current_qty = current["net_qty"]
    current_cost = current["total_cost"]

    # Calcular nova posição
    new_qty = round(current_qty + signed_qty, 6)

    # VWAP: custo acumulado só cresce em compras, reduz em vendas proporcionalmente
    if order["side"] == "buy":
        new_cost = current_cost + (qty * price)
    else:
        # Venda: reduz custo proporcionalmente à fração vendida
        if abs(current_qty) > 0:
            cost_per_unit = current_cost / abs(current_qty)
        else:
            cost_per_unit = price
        new_cost = max(0.0, current_cost - (qty * cost_per_unit))

    # avg_price = custo total / quantidade absoluta
    if abs(new_qty) > 1e-9:
        new_avg_price = round(new_cost / abs(new_qty), 6)
    else:
        new_avg_price = 0.0
        new_cost = 0.0

    STORE.upsert_position(
        symbol=sym,
        net_qty=new_qty,
        avg_price=new_avg_price,
        total_cost=round(new_cost, 6),
    )


def get_positions() -> list[dict]:
    """Retorna posições com net_qty != 0."""
    return [
        p for p in STORE.positions.values()
        if abs(p["net_qty"]) > 1e-9
    ]


def get_pnl() -> dict:
    """
    Calcula exposição bruta e PnL estimado.

    unrealized_pnl é um placeholder (1% do custo total).
    Para PnL real, substituir pelo mark-to-market com preço atual do exchange.
    """
    positions = get_positions()
    gross_exposure = 0.0
    unrealized_pnl = 0.0

    for pos in positions:
        exposure = abs(pos["net_qty"] * pos["avg_price"])
        gross_exposure += exposure
        # Placeholder: 1% do custo como PnL estimado
        # TODO: substituir por (last_price - avg_price) * net_qty via API do exchange
        unrealized_pnl += pos["total_cost"] * 0.01

    return {
        "positions": len(positions),
        "gross_exposure": round(gross_exposure, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "pnl_note": "unrealized_pnl é estimativa de 1% do custo. Para mark-to-market real, integrar com exchange API.",
    }
