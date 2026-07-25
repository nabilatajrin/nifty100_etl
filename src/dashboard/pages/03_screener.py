"""Screener screen — sliders, presets, live results, CSV export (Sprint 4, Day 24)."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_companies
from src.screener.engine import load_config
from src.screener.run_presets import latest_ratios
from src.screener.composite_score import composite_score

st.set_page_config(page_title="Screener — Nifty 100 Analytics", layout="wide")
st.title("🔎 Financial Screener")

config = load_config()
companies = get_companies()


@st.cache_data(ttl=600)
def _load_screener_universe() -> pd.DataFrame:
    import sqlite3, os
    conn = sqlite3.connect(os.getenv("DB_PATH", "data/nifty100.db"))
    df = latest_ratios(conn)
    sec = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()
    df = df.merge(sec, on="company_id", how="left")
    df["composite_quality_score"] = composite_score(df)
    return df


df = _load_screener_universe()

# --- slider metric -> (label, min, max, default, step) ---
SLIDERS = {
    "roe":            ("ROE min (%)", -20, 80, 0, 1),
    "de":             ("D/E max", 0.0, 10.0, 10.0, 0.1),
    "fcf":            ("FCF min (₹ Cr)", -2000, 2000, -2000, 50),
    "rev_cagr_5yr":   ("Revenue CAGR 5yr min (%)", -20, 60, -20, 1),
    "pat_cagr_5yr":   ("PAT CAGR 5yr min (%)", -50, 80, -50, 1),
    "opm":            ("OPM min (%)", -20, 60, -20, 1),
    "pe":             ("P/E max", 0, 100, 100, 1),
    "pb":             ("P/B max", 0.0, 20.0, 20.0, 0.5),
    "dividend_yield": ("Dividend Yield min (%)", 0.0, 8.0, 0.0, 0.1),
    "icr":            ("ICR min", 0, 30, 0, 1),
}

PRESET_LABELS = {
    "quality_compounder": "Quality",
    "value_pick": "Value",
    "growth_accelerator": "Growth",
    "dividend_champion": "Dividend",
    "debt_free_bluechip": "Debt-Free",
    "turnaround_watch": "Turnaround",
}

if "slider_vals" not in st.session_state:
    st.session_state.slider_vals = {k: v[3] for k, v in SLIDERS.items()}

# --- Preset buttons ---
st.write("**Quick presets:**")
btn_cols = st.columns(len(PRESET_LABELS))
for i, (preset_key, label) in enumerate(PRESET_LABELS.items()):
    if btn_cols[i].button(label):
        preset_thresholds = config["presets"][preset_key]
        for k in SLIDERS:
            if k in preset_thresholds:
                st.session_state.slider_vals[k] = preset_thresholds[k]

st.divider()

# --- Sidebar sliders ---
st.sidebar.header("Filter thresholds")
thresholds = {}
for key, (label, lo, hi, default, step) in SLIDERS.items():
    val = st.sidebar.slider(
        label, min_value=lo, max_value=hi,
        value=st.session_state.slider_vals.get(key, default), step=step,
    )
    st.session_state.slider_vals[key] = val
    thresholds[key] = val

# --- Apply filters live ---
sectors = df["broad_sector"]
sectors.index = df.index
mask = pd.Series(True, index=df.index)
metrics_cfg = config["metrics"]
for key, threshold in thresholds.items():
    meta = metrics_cfg.get(key)
    if not meta or meta["column"] not in df.columns:
        continue
    col = meta["column"]
    value = df[col]
    if key == "icr":
        keep = value.isna() | (value >= threshold)
    elif key == "de":
        keep = value.notna() & (value <= threshold)
        keep = keep | sectors.eq("Financials")
    elif meta["direction"] == "min":
        keep = value.notna() & (value >= threshold)
    else:
        keep = value.notna() & (value <= threshold)
    mask &= keep

result = df[mask].sort_values("composite_quality_score", ascending=False)
result = result.merge(companies[["id", "company_name"]], left_on="company_id",
                      right_on="id", how="left")

st.subheader(f"{len(result)} companies match your filters")

display_cols = ["company_id", "company_name", "broad_sector",
                "composite_quality_score", "return_on_equity_pct",
                "debt_to_equity", "revenue_cagr_5yr", "free_cash_flow_cr"]
display_cols = [c for c in display_cols if c in result.columns]

st.dataframe(result[display_cols].reset_index(drop=True), use_container_width=True)

csv = result[display_cols].to_csv(index=False).encode("utf-8")
st.download_button("⬇ Download CSV", data=csv, file_name="screener_results.csv",
                   mime="text/csv")
