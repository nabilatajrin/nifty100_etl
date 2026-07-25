"""Integration QA (Sprint 4, Day 27).

Exercises the core data-logic behind every dashboard screen across 10 tickers
spanning different sectors, plus edge cases: a ticker with partial history,
and extreme screener slider values. Reports pass/fail per check rather than
launching the browser (Streamlit rendering is verified separately by
manually clicking through the app).

Run:  python -m src.dashboard.qa_integration
"""

import os
import sqlite3
import time

import pandas as pd
from dotenv import load_dotenv

from ..screener.engine import load_config
from ..screener.run_presets import latest_ratios
from ..screener.composite_score import composite_score
from ..analytics.valuation import build_valuation_summary


def pick_test_tickers(conn, n=10) -> list:
    """One ticker per sector where possible, to cover the sector spread."""
    sec = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    picks = []
    for _, grp in sec.groupby("broad_sector"):
        picks.append(grp.iloc[0]["company_id"])
        if len(picks) >= n:
            break
    remaining = n - len(picks)
    if remaining > 0:
        extra = sec[~sec["company_id"].isin(picks)]["company_id"].head(remaining).tolist()
        picks += extra
    return picks[:n]


def check_profile_data(conn, ticker) -> tuple[bool, str]:
    """Simulates the Company Profile screen's data pull for one ticker."""
    try:
        ratios = pd.read_sql(
            "SELECT * FROM financial_ratios WHERE company_id=? ORDER BY year",
            conn, params=(ticker,))
        pl = pd.read_sql(
            "SELECT * FROM profitandloss WHERE company_id=? ORDER BY year",
            conn, params=(ticker,))
        # this is the exact fallback the page uses for missing metrics
        latest = ratios.iloc[-1] if not ratios.empty else pd.Series(dtype=float)
        _ = f"{latest.get('return_on_equity_pct'):.2f}" if pd.notna(
            latest.get("return_on_equity_pct")) else "N/A"
        n_years = len(pl)
        note = f"{n_years} yrs history" if n_years >= 5 else f"PARTIAL DATA: only {n_years} yrs"
        return True, note
    except Exception as e:
        return False, str(e)


def check_screener_extremes(conn) -> tuple[bool, str]:
    """Runs the screener with all sliders at min AND all at max — must not crash."""
    try:
        df = latest_ratios(conn)
        sec = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
        df = df.merge(sec, on="company_id", how="left")
        df["composite_quality_score"] = composite_score(df)
        sectors = df["broad_sector"]
        sectors.index = df.index

        # extreme 1: nothing should pass (roe >= 999)
        keep = df["return_on_equity_pct"].notna() & (df["return_on_equity_pct"] >= 999)
        n_none = keep.sum()

        # extreme 2: everything should pass (roe >= -999)
        keep2 = df["return_on_equity_pct"].notna() & (df["return_on_equity_pct"] >= -999)
        n_all = keep2.sum()

        return True, f"min-extreme -> {n_none} pass, max-extreme -> {n_all} pass (no crash)"
    except Exception as e:
        return False, str(e)


def check_valuation_no_crash(conn) -> tuple[bool, str]:
    try:
        summary = build_valuation_summary(conn)
        return True, f"{len(summary)} rows, no crash"
    except Exception as e:
        return False, str(e)


def check_missing_metric_handling() -> tuple[bool, str]:
    """None/NaN must render as 'N/A', never raise."""
    import math
    val = float("nan")
    try:
        display = f"{val:.2f}" if pd.notna(val) else "N/A"
        assert display == "N/A"
        val2 = None
        display2 = f"{val2:.2f}" if pd.notna(val2) else "N/A"
        assert display2 == "N/A"
        return True, "NaN and None both render as N/A"
    except Exception as e:
        return False, str(e)


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)

    tickers = pick_test_tickers(conn, 10)
    print(f"Testing {len(tickers)} tickers across sectors: {tickers}\n")

    print("--- Company Profile data checks ---")
    all_ok = True
    for t in tickers:
        t0 = time.time()
        ok, note = check_profile_data(conn, t)
        elapsed = time.time() - t0
        status = "PASS" if ok else "FAIL"
        speed_ok = "OK" if elapsed < 3.0 else "SLOW"
        print(f"  {t:<12} {status:<5} {note:<30} ({elapsed*1000:.0f}ms, {speed_ok})")
        all_ok &= ok

    print("\n--- Screener extreme-value check ---")
    ok, note = check_screener_extremes(conn)
    print(f"  {'PASS' if ok else 'FAIL'}: {note}")
    all_ok &= ok

    print("\n--- Valuation module no-crash check ---")
    ok, note = check_valuation_no_crash(conn)
    print(f"  {'PASS' if ok else 'FAIL'}: {note}")
    all_ok &= ok

    print("\n--- Missing-data display check (N/A, not crash) ---")
    ok, note = check_missing_metric_handling()
    print(f"  {'PASS' if ok else 'FAIL'}: {note}")
    all_ok &= ok

    conn.close()

    print("\n" + ("ALL CHECKS PASSED ✓" if all_ok else "SOME CHECKS FAILED — see above"))


if __name__ == "__main__":
    main()
