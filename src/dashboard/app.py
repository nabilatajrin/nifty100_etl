"""Nifty 100 Analytics — Streamlit entry point (Sprint 4, Day 22).

Run:  streamlit run src/dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Nifty 100 Financial Intelligence Platform")
st.caption(
    "Use the sidebar to navigate: Home, Company Profile, Screener, Peer "
    "Comparison, Trend Analysis, Sector Analysis, Capital Allocation Map, "
    "Annual Reports."
)

st.markdown("""
### Welcome

This dashboard covers all 92 Nifty 100 companies with financial ratios,
a multi-preset screener, peer comparison, and sector analytics.

**Navigate using the pages listed in the left sidebar.**

*Note: stock price and market capitalisation figures in this dashboard are
SIMULATED for demonstration purposes.*
""")
