"""Sector Analysis screen — bubble chart + median KPI bars (Sprint 4, Day 25)."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_sectors

st.set_page_config(page_title="Sector Analysis — Nifty 100 Analytics", layout="wide")
st.title("🏭 Sector Analysis")


@st.cache_data(ttl=600)
def _sector_frame() -> pd.DataFrame:
    import sqlite3, os

    conn = sqlite3.connect(os.getenv("DB_PATH", "data/nifty100.db"))
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    fr = fr.sort_values("year").groupby("company_id").tail(1)
    pl = pd.read_sql("SELECT company_id, year, sales FROM profitandloss", conn)
    pl = pl.sort_values("year").groupby("company_id").tail(1)
    sec = pd.read_sql("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
    try:
        mc = pd.read_sql(
            "SELECT company_id, year, market_cap_crore FROM market_cap", conn
        )
        mc = mc.sort_values("year").groupby("company_id").tail(1)
    except Exception:
        mc = pd.DataFrame(columns=["company_id", "market_cap_crore"])
    conn.close()
    df = fr.merge(pl[["company_id", "sales"]], on="company_id", how="left")
    df = df.merge(sec, on="company_id", how="left")
    df = df.merge(mc[["company_id", "market_cap_crore"]], on="company_id", how="left")
    return df


df = _sector_frame()
sectors = sorted(df["broad_sector"].dropna().unique())

selected_sector = st.selectbox("Sector", ["All"] + sectors)
plot_df = df if selected_sector == "All" else df[df["broad_sector"] == selected_sector]

st.subheader("Revenue vs ROE (bubble size = Market Cap)")
if not plot_df.empty and plot_df["sales"].notna().any():
    fig = px.scatter(
        plot_df,
        x="sales",
        y="return_on_equity_pct",
        size=plot_df["market_cap_crore"].fillna(
            plot_df["market_cap_crore"].median() or 1000
        ),
        color="sub_sector",
        hover_name="company_id",
        labels={"sales": "Revenue (₹ Cr)", "return_on_equity_pct": "ROE (%)"},
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Not enough data to render the bubble chart.")

st.divider()

st.subheader("Sector Median KPIs")
median_df = (
    df.groupby("broad_sector")[
        ["return_on_equity_pct", "debt_to_equity", "revenue_cagr_5yr"]
    ]
    .median()
    .reset_index()
)

if not median_df.empty:
    fig2 = px.bar(
        median_df,
        x="broad_sector",
        y="return_on_equity_pct",
        labels={"return_on_equity_pct": "Median ROE (%)", "broad_sector": "Sector"},
    )
    fig2.update_layout(height=400, xaxis_tickangle=-30)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No sector data available.")
