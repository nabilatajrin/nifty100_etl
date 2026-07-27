"""Peer Comparison screen — radar chart + side-by-side KPI table (Sprint 4, Day 24)."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_peer_groups, get_peers, get_companies

st.set_page_config(page_title="Peer Comparison — Nifty 100 Analytics", layout="wide")
st.title("🆚 Peer Comparison")

groups = get_peer_groups()
if not groups:
    st.warning("No peer groups found. Run Sprint 3 Day 18 (peer.py) first.")
    st.stop()

group = st.selectbox("Peer group", groups)
pct = get_peers(group)
companies = get_companies()

if pct.empty:
    st.info("No peer percentile data for this group.")
    st.stop()

# wide pivot: company_id x metric -> value
wide = pct.pivot_table(
    index="company_id", columns="metric", values="value", aggfunc="first"
)
wide = wide.merge(
    companies[["id", "company_name"]], left_index=True, right_on="id", how="left"
)
wide = wide.rename(columns={"id": "company_id"}).set_index("company_id")

member_ids = wide.index.tolist()
selected_company = st.selectbox("Company (for radar chart)", member_ids)

# --- Radar chart: company vs peer group average ---
AXES = [
    "return_on_equity_pct",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "interest_coverage",
]
axes_present = [a for a in AXES if a in wide.columns]

if axes_present and selected_company in wide.index:
    company_vals = wide.loc[selected_company, axes_present].fillna(0).tolist()
    peer_avg = wide[axes_present].mean().fillna(0).tolist()

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=company_vals + [company_vals[0]],
            theta=axes_present + [axes_present[0]],
            fill="toself",
            name=selected_company,
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=peer_avg + [peer_avg[0]],
            theta=axes_present + [axes_present[0]],
            name=f"{group} average",
            line=dict(dash="dash"),
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        height=500,
        title=f"{selected_company} vs {group} average",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Not enough metric data to render the radar chart for this selection.")

st.divider()

# --- Side-by-side table, benchmark row highlighted ---
st.subheader(f"All companies in {group}")

# find benchmark from peer_groups table if available
benchmark = None
try:
    import sqlite3, os

    conn = sqlite3.connect(os.getenv("DB_PATH", "data/nifty100.db"))
    peers_raw = pd.read_sql("SELECT * FROM peer_groups", conn)
    conn.close()
    group_col = next(
        (c for c in peers_raw.columns if "group" in c.lower() and "name" in c.lower()),
        None,
    )
    bench_col = next((c for c in peers_raw.columns if "benchmark" in c.lower()), None)
    if group_col and bench_col:
        grp_rows = peers_raw[peers_raw[group_col] == group]
        true_rows = grp_rows[
            grp_rows[bench_col].astype(str).str.upper().isin(["TRUE", "1", "YES"])
        ]
        if not true_rows.empty:
            benchmark = true_rows.iloc[0]["company_id"]
except Exception:
    pass

display_df = wide.reset_index()[["company_id", "company_name"] + axes_present]


def _highlight_benchmark(row):
    if benchmark and row["company_id"] == benchmark:
        return ["background-color: #FFD966"] * len(row)
    return [""] * len(row)


st.dataframe(
    display_df.style.apply(_highlight_benchmark, axis=1),
    use_container_width=True,
)
if benchmark:
    st.caption(f"🏅 Benchmark company: **{benchmark}** (highlighted above)")
