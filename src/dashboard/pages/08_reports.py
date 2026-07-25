"""Annual Reports screen — clickable links, 404 detection (Sprint 4, Day 25)."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_companies, get_documents

st.set_page_config(page_title="Annual Reports — Nifty 100 Analytics", layout="wide")
st.title("📄 Annual Reports")

companies = get_companies()
options = [f"{r.id} — {r.company_name}" for r in companies.itertuples()]
search = st.text_input("Search company", "")
filtered = [o for o in options if search.upper() in o.upper()] if search else options

if not filtered:
    st.warning("Ticker not found — please try another")
    st.stop()

selection = st.selectbox("Company", filtered)
ticker = selection.split(" — ")[0]

docs = get_documents(ticker)

if docs.empty:
    st.info("No annual report links available for this company.")
    st.stop()


@st.cache_data(ttl=3600)
def _check_url(url: str) -> bool:
    """True if the URL appears reachable. Cached for an hour to avoid re-checking."""
    if not url or pd.isna(url):
        return False
    try:
        resp = requests.head(url, timeout=4, allow_redirects=True)
        return resp.status_code == 200
    except Exception:
        return False


st.subheader(f"Annual Reports — {ticker}")

check_live = st.checkbox("Verify links are live (slower)", value=False)

for _, row in docs.sort_values("Year", ascending=False).iterrows():
    year = row.get("Year")
    url = row.get("Annual_Report")
    col1, col2 = st.columns([1, 4])
    with col1:
        st.write(f"**{year}**")
    with col2:
        if pd.isna(url) or not url:
            st.markdown("🔴 **Report unavailable**")
        elif check_live and not _check_url(url):
            st.markdown(f"🔴 **Report unavailable** ~~{url}~~")
        else:
            st.markdown(f"[📎 View Annual Report ({year})]({url})")
