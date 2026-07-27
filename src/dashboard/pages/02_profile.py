"""Company Profile screen — search, KPI tiles, trend charts, pros/cons (Sprint 4, Day 23)."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_pros_cons

st.set_page_config(page_title="Company Profile — Nifty 100 Analytics", layout="wide")
st.title("🏢 Company Profile")

companies = get_companies()
options = [f"{row.id} — {row.company_name}" for row in companies.itertuples()]

search = st.text_input("Search by company name or ticker", "")
filtered = [o for o in options if search.upper() in o.upper()] if search else options

selection = st.selectbox("Select a company", filtered) if filtered else None

if search and not filtered:
    st.warning("Ticker not found — please try another")
    st.stop()

if not selection:
    st.info("Type a company name or ticker above to begin.")
    st.stop()

ticker = selection.split(" — ")[0]
row = companies[companies["id"] == ticker]

if row.empty:
    st.warning("Ticker not found — please try another")
    st.stop()

row = row.iloc[0]

# --- Company card ---
st.subheader(f"{row['company_name']} ({ticker})")
c1, c2 = st.columns([1, 2])
with c1:
    st.markdown(f"**Sector:** {row.get('broad_sector', 'N/A')}")
    st.markdown(f"**Sub-sector:** {row.get('sub_sector', 'N/A')}")
    st.markdown(f"**NSE Ticker:** {ticker}")
with c2:
    about = row.get("about_company")
    st.markdown(
        f"**About:** {about if pd.notna(about) else 'No description available.'}"
    )

st.divider()

ratios = get_ratios(ticker)
pl = get_pl(ticker)

if ratios.empty:
    st.warning("No financial data available for this company.")
    st.stop()

latest = ratios.sort_values("year").iloc[-1]


# --- 6 KPI tiles ---
def _fmt(val, suffix=""):
    return f"{val:.2f}{suffix}" if pd.notna(val) else "N/A"


k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("ROE", _fmt(latest.get("return_on_equity_pct"), "%"))
k2.metric("ROCE", _fmt(latest.get("return_on_capital_employed_pct"), "%"))
k3.metric("Net Profit Margin", _fmt(latest.get("net_profit_margin_pct"), "%"))
k4.metric("D/E", _fmt(latest.get("debt_to_equity")))
k5.metric("Revenue CAGR 5yr", _fmt(latest.get("revenue_cagr_5yr"), "%"))
k6.metric("FCF (₹ Cr)", _fmt(latest.get("free_cash_flow_cr")))

st.divider()

# --- 10-year Revenue & Net Profit bar chart ---
if not pl.empty:
    hist = pl.sort_values("year").tail(10)
    st.subheader("Revenue & Net Profit — Last 10 Years")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=hist["year"], y=hist["sales"], name="Revenue"))
    fig.add_trace(go.Bar(x=hist["year"], y=hist["net_profit"], name="Net Profit"))
    fig.update_layout(barmode="group", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # --- ROE / ROCE dual-axis line chart ---
    hist_r = ratios.sort_values("year").tail(10)
    st.subheader("ROE & ROCE Trend — Last 10 Years")
    fig2 = go.Figure()
    fig2.add_trace(
        go.Scatter(
            x=hist_r["year"],
            y=hist_r["return_on_equity_pct"],
            name="ROE %",
            mode="lines+markers",
        )
    )
    if "return_on_capital_employed_pct" in hist_r.columns:
        fig2.add_trace(
            go.Scatter(
                x=hist_r["year"],
                y=hist_r["return_on_capital_employed_pct"],
                name="ROCE %",
                mode="lines+markers",
            )
        )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Fewer than the expected years of history are available for this company.")

st.divider()

# --- Pros & Cons badges ---
st.subheader("Pros & Cons")
pc = get_pros_cons(ticker)
if pc.empty:
    st.caption("No pros/cons recorded for this company yet.")
else:
    col_p, col_c = st.columns(2)
    with col_p:
        for p in pc["pros"].dropna():
            st.success(f"✅ {p}")
    with col_c:
        for c in pc["cons"].dropna():
            st.error(f"❌ {c}")
