"""Shared, cached database access layer for the Streamlit dashboard (Sprint 4, Day 22).

Every query function is wrapped with @st.cache_data(ttl=600) per spec, so
repeated navigation between screens doesn't re-hit SQLite every time.
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _db_path() -> str:
    return os.getenv("DB_PATH", "data/nifty100.db")


def _connect():
    return sqlite3.connect(_db_path())


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """All 92 companies with sector info."""
    conn = _connect()
    df = pd.read_sql(
        """SELECT c.id, c.company_name, c.about_company, c.face_value,
                  s.broad_sector, s.sub_sector
           FROM companies c
           LEFT JOIN sectors s ON s.company_id = c.id
           ORDER BY c.id""",
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker: str, year: str | None = None) -> pd.DataFrame:
    """financial_ratios rows for a ticker; all years, or one if `year` given."""
    conn = _connect()
    if year:
        df = pd.read_sql(
            "SELECT * FROM financial_ratios WHERE company_id = ? AND year = ?",
            conn, params=(ticker, year))
    else:
        df = pd.read_sql(
            "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year",
            conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year",
        conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql(
        "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year",
        conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql(
        "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year",
        conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql("SELECT * FROM sectors", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    """All companies + percentile data within one peer group."""
    conn = _connect()
    df = pd.read_sql(
        "SELECT * FROM peer_percentiles WHERE peer_group_name = ?",
        conn, params=(group_name,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peer_groups() -> list:
    conn = _connect()
    try:
        groups = pd.read_sql(
            "SELECT DISTINCT peer_group_name FROM peer_percentiles ORDER BY peer_group_name",
            conn)["peer_group_name"].tolist()
    except Exception:
        groups = []
    conn.close()
    return groups


@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    conn = _connect()
    try:
        df = pd.read_sql(
            "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year",
            conn, params=(ticker,))
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pros_cons(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql(
        "SELECT * FROM prosandcons WHERE company_id = ?", conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_documents(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql(
        "SELECT * FROM documents WHERE company_id = ? ORDER BY Year DESC",
        conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_capital_allocation() -> pd.DataFrame:
    """Reads the Day 11/12 output CSV if present, else empty frame."""
    path = "output/capital_allocation.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=["company_id", "year", "cfo_sign", "cfi_sign",
                                 "cff_sign", "pattern_label"])
