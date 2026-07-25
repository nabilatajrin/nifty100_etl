"""Trend Analysis screen — multi-metric overlay with YoY change (Sprint 4, Day 25)."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_companies, get_ratios

st.set_page_config(page_title="Trend Analysis — Nifty 100 Analytics", layout="wide")
st.title("📈 Trend Analysis")

companies = get_companies()
options = [f"{r.id} — {r.company_name}" for r in companies.itertuples()]
search = st.text_input("Search company", "")
filtered = [o for o in options if search.upper() in o.upper()] if search else options

if not filtered:
    st.warning("Ticker not found — please try another")
    st.stop()

selection = st.selectbox("Company", filtered)
ticker = selection.split(" — ")[0]

METRIC_CHOICES = {
    "ROE (%)": "return_on_equity_pct",
    "OPM (%)": "operating_profit_margin_pct",
    "NPM (%)": "net_profit_margin_pct",
    "D/E": "debt_to_equity",
    "Revenue CAGR 5yr (%)": "revenue_cagr_5yr",
    "PAT CAGR 5yr (%)": "pat_cagr_5yr",
    "FCF (₹ Cr)": "free_cash_flow_cr",
}

selected_labels = st.multiselect(
    "Metrics to overlay (up to 3)", list(METRIC_CHOICES.keys()),
    default=["ROE (%)"], max_selections=3,
)

ratios = get_ratios(ticker).sort_values("year").tail(10)

if ratios.empty:
    st.info("No historical ratio data available for this company.")
    st.stop()

if not selected_labels:
    st.info("Select at least one metric to plot.")
    st.stop()

fig = go.Figure()
for label in selected_labels:
    col = METRIC_CHOICES[label]
    if col not in ratios.columns:
        continue
    series = ratios[col]
    yoy = series.pct_change() * 100

    fig.add_trace(go.Scatter(
        x=ratios["year"], y=series, mode="lines+markers", name=label,
        text=[f"{v:+.1f}% YoY" if pd.notna(v) else "" for v in yoy],
        hovertemplate="%{x}: %{y:.2f}<br>%{text}<extra></extra>",
    ))

fig.update_layout(height=500, title=f"{ticker} — {len(ratios)}-Year Trend")
st.plotly_chart(fig, use_container_width=True)
st.caption("Hover over points to see year-over-year % change.")
