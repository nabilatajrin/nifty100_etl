"""Home screen — summary KPIs, sector breakdown, top companies (Sprint 4, Day 23)."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_companies, get_sectors
from src.screener.composite_score import composite_score

st.set_page_config(page_title="Home — Nifty 100 Analytics", layout="wide")
st.title("🏠 Home / Overview")


@st.cache_data(ttl=600)
def _latest_ratios_with_sector(year: str | None = None) -> pd.DataFrame:
    import sqlite3, os

    conn = sqlite3.connect(os.getenv("DB_PATH", "data/nifty100.db"))
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    if year:
        fr = fr[fr["year"].str.startswith(year)]
    fr = fr.sort_values("year").groupby("company_id").tail(1).reset_index(drop=True)
    sec = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    try:
        mc = pd.read_sql("SELECT company_id, year, pe_ratio FROM market_cap", conn)
        mc = mc.sort_values("year").groupby("company_id").tail(1)
        fr = fr.merge(mc[["company_id", "pe_ratio"]], on="company_id", how="left")
    except Exception:
        fr["pe_ratio"] = None
    conn.close()
    return fr.merge(sec, on="company_id", how="left")


# --- Year selector (sidebar) ---
years = [str(y) for y in range(2019, 2025)]
selected_year = st.sidebar.selectbox("Year", years, index=len(years) - 1)

df = _latest_ratios_with_sector(selected_year)

if df.empty:
    st.warning(
        f"No data available for {selected_year}. Showing latest available instead."
    )
    df = _latest_ratios_with_sector(None)

df["composite_quality_score"] = composite_score(df)

# --- 6 KPI tiles ---
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric(
    "Avg ROE", f"{df['return_on_equity_pct'].mean():.1f}%" if not df.empty else "N/A"
)
c2.metric(
    "Median P/E",
    f"{df['pe_ratio'].median():.1f}x" if df["pe_ratio"].notna().any() else "N/A",
)
c3.metric(
    "Median D/E", f"{df['debt_to_equity'].median():.2f}" if not df.empty else "N/A"
)
c4.metric("Total Companies", f"{len(df)}")
c5.metric(
    "Median Rev CAGR 5yr",
    f"{df['revenue_cagr_5yr'].median():.1f}%" if not df.empty else "N/A",
)
c6.metric("Debt-Free Companies", f"{(df['debt_to_equity'] == 0).sum()}")

st.divider()

# --- Sector breakdown donut + Top-5 table ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Sector Breakdown")
    sectors = get_sectors()
    counts = sectors["broad_sector"].value_counts().reset_index()
    counts.columns = ["broad_sector", "count"]
    if not counts.empty:
        fig = px.pie(counts, names="broad_sector", values="count", hole=0.5)
        fig.update_layout(height=400, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sector data available.")

with col_right:
    st.subheader("Top 5 by Composite Quality Score")
    top5 = df.sort_values("composite_quality_score", ascending=False).head(5)
    cols_show = [
        c
        for c in [
            "company_id",
            "composite_quality_score",
            "return_on_equity_pct",
            "debt_to_equity",
        ]
        if c in top5.columns
    ]
    if not top5.empty:
        st.dataframe(top5[cols_show].reset_index(drop=True), use_container_width=True)
    else:
        st.info("No data available for the selected year.")
