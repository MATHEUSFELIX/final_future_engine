"""
Future Engine — Streamlit Dashboard
"""
import streamlit as st
import requests

API_BASE = "http://api:8000"

st.set_page_config(page_title="Future Engine", layout="wide")
st.title("Future Engine Dashboard")


def safe_get(url: str) -> dict:
    try:
        r = requests.get(url, timeout=3)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def safe_post(url: str, payload: dict) -> dict:
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# --- Status bar ---
status = safe_get(f"{API_BASE}/ops/status")

col1, col2, col3, col4 = st.columns(4)
with col1:
    mode = status.get("exchange_mode", "unknown")
    st.metric("Exchange Mode", mode)
with col2:
    live = status.get("live_trading_enabled", False)
    label = "LIVE ENABLED" if live else "Paper Safe"
    color = "error" if live else "success"
    if live:
        st.error(f"LIVE_TRADING: {live}")
    else:
        st.success(f"LIVE_TRADING: {live}")
with col3:
    st.metric("Orders", status.get("orders", 0))
with col4:
    st.metric("Events", status.get("events", 0))

st.divider()

# --- Signal generation ---
st.subheader("Signal Generation")
symbols_input = st.text_input("Symbols (comma separated)", "BTCUSDT,ETHUSDT,SOLUSDT")
timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=4)

if st.button("Generate Signals"):
    symbols = [s.strip() for s in symbols_input.split(",") if s.strip()]
    result = safe_post(f"{API_BASE}/signals/generate", {"symbols": symbols, "timeframe": timeframe})
    if "signals" in result:
        st.dataframe(result["signals"])
    else:
        st.json(result)

st.divider()

# --- Autotrade ---
st.subheader("Autotrade")
if st.button("Run Autotrade Cycle"):
    symbols = [s.strip() for s in symbols_input.split(",") if s.strip()]
    result = safe_post(f"{API_BASE}/autotrade/run", {"symbols": symbols, "timeframe": timeframe})
    st.json(result)

st.divider()

# --- Portfolio ---
st.subheader("Portfolio")
col_pos, col_pnl = st.columns(2)
with col_pos:
    if st.button("Refresh Positions"):
        pos = safe_get(f"{API_BASE}/portfolio/positions")
        st.json(pos)
with col_pnl:
    if st.button("Refresh PnL"):
        pnl = safe_get(f"{API_BASE}/portfolio/pnl")
        st.json(pnl)

st.divider()

# --- Orders ---
st.subheader("Recent Orders")
if st.button("Refresh Orders"):
    orders = safe_get(f"{API_BASE}/ops/orders")
    if "orders" in orders:
        st.dataframe(orders["orders"])
    else:
        st.json(orders)
