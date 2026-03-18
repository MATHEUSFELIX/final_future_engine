"""
store.py — Persistência SQLite para o Future Engine

Substitui o STORE dict in-memory por um SQLiteStore que persiste
ordens, eventos e posições entre restarts da API.

Feature resolvida: F002
"""
from __future__ import annotations
import sqlite3
import json
import os
from pathlib import Path
from typing import Any

DB_PATH = os.getenv("DB_PATH", "/tmp/future_engine.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    """Cria as tabelas se não existirem."""
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                price REAL NOT NULL,
                reason TEXT,
                provider TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                symbol TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                net_qty REAL NOT NULL DEFAULT 0.0,
                avg_price REAL NOT NULL DEFAULT 0.0,
                total_cost REAL NOT NULL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS signals_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


# Inicializa o banco ao importar o módulo
_init_db()


class _Store:
    """Interface compatível com o STORE dict original, mas com SQLite por baixo."""

    # --- Sinais (ainda em memória — voláteis por design) ---
    _signals: list[dict] = []

    @property
    def signals(self) -> list[dict]:
        return self._signals

    @signals.setter
    def signals(self, value: list[dict]) -> None:
        self._signals = value

    # --- Ordens (persistidas) ---
    @property
    def orders(self) -> list[dict]:
        with _get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM orders ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def append_order(self, order: dict) -> None:
        with _get_conn() as conn:
            conn.execute(
                """INSERT INTO orders (symbol, side, quantity, mode, status, price, reason, provider)
                   VALUES (:symbol, :side, :quantity, :mode, :status, :price, :reason, :provider)""",
                {
                    "symbol": order.get("symbol", ""),
                    "side": order.get("side", ""),
                    "quantity": order.get("quantity", 0.0),
                    "mode": order.get("mode", "paper"),
                    "status": order.get("status", ""),
                    "price": order.get("price", 0.0),
                    "reason": order.get("reason", ""),
                    "provider": order.get("provider", "paper"),
                },
            )

    # --- Eventos (persistidos) ---
    @property
    def events(self) -> list[dict]:
        with _get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def append_event(self, event: dict) -> None:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO events (type, symbol, status) VALUES (:type, :symbol, :status)",
                {
                    "type": event.get("type", ""),
                    "symbol": event.get("symbol", ""),
                    "status": event.get("status", ""),
                },
            )

    # --- Posições (persistidas) ---
    @property
    def positions(self) -> dict[str, dict]:
        with _get_conn() as conn:
            rows = conn.execute("SELECT * FROM positions").fetchall()
        return {r["symbol"]: dict(r) for r in rows}

    def upsert_position(self, symbol: str, net_qty: float, avg_price: float, total_cost: float) -> None:
        with _get_conn() as conn:
            conn.execute(
                """INSERT INTO positions (symbol, net_qty, avg_price, total_cost)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(symbol) DO UPDATE SET
                     net_qty=excluded.net_qty,
                     avg_price=excluded.avg_price,
                     total_cost=excluded.total_cost,
                     updated_at=CURRENT_TIMESTAMP""",
                (symbol, net_qty, avg_price, total_cost),
            )

    def get_position(self, symbol: str) -> dict | None:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM positions WHERE symbol = ?", (symbol,)
            ).fetchone()
        return dict(row) if row else None

    # --- Compatibilidade com código legado que usa STORE['orders'].append() ---
    def __getitem__(self, key: str) -> Any:
        if key == "signals":
            return self._signals
        if key == "orders":
            return _OrderProxy(self)
        if key == "events":
            return _EventProxy(self)
        if key == "positions":
            return self.positions
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "signals":
            self._signals = value
        else:
            raise KeyError(f"Chave '{key}' não suporta atribuição direta no SQLiteStore.")


class _OrderProxy(list):
    """Proxy para manter compatibilidade com STORE['orders'].append(order)."""
    def __init__(self, store: _Store):
        self._store = store
        super().__init__(store.orders)

    def append(self, order: dict) -> None:
        self._store.append_order(order)


class _EventProxy(list):
    """Proxy para manter compatibilidade com STORE['events'].append(event)."""
    def __init__(self, store: _Store):
        self._store = store
        super().__init__(store.events)

    def append(self, event: dict) -> None:
        self._store.append_event(event)


STORE = _Store()
