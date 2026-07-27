"""Capital Allocation Map — treemap by 8 patterns (Sprint 4, Day 25)."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_capital_allocation, get_companies

st.set_page_config(
    page_title="Capital Allocation Map — Nifty 100 Analytics", layout="wide"
)
st.title("🗺️ Capital Allocation Map")

cap = get_capital_allocation()
companies = get_companies()

if cap.empty:
    st.warning(
        "No capital_allocation.csv found. Run Sprint 2 Day 12 "
        "(compute_ratios.py) to generate it first."
    )
    st.stop()

# latest year per company
latest = cap.sort_values("year").groupby("company_id").tail(1)
latest = latest.merge(
    companies[["id", "broad_sector"]], left_on="company_id", right_on="id", how="left"
)

st.subheader("92 Companies by Capital Allocation Pattern")
fig = px.treemap(
    latest,
    path=["pattern_label", "company_id"],
    color="pattern_label",
)
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Explore a pattern")
patterns = sorted(latest["pattern_label"].dropna().unique())
if patterns:
    chosen = st.selectbox("Pattern", patterns)
    subset = latest[latest["pattern_label"] == chosen]
    st.write(f"**{len(subset)} companies** with pattern **{chosen}**:")
    st.dataframe(
        subset[
            ["company_id", "broad_sector", "cfo_sign", "cfi_sign", "cff_sign"]
        ].reset_index(drop=True),
        use_container_width=True,
    )
else:
    st.info("No pattern data available.")
