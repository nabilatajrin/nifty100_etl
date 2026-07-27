"""Screener preview (Sprint 2, Day 14).

A simple filter over the latest-year financial_ratios to sanity-check the KPIs:
"Quality" screen = ROE > 15% AND D/E < 1. Expect roughly 15-50 companies.
Run:  python -m src.analytics.screener_preview
"""

import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv


def latest_ratios(conn) -> pd.DataFrame:
    """Latest-year row per company from financial_ratios."""
    df = pd.read_sql("SELECT * FROM financial_ratios", conn)
    return df.sort_values("year").groupby("company_id").tail(1)


def main() -> None:
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)
    latest = latest_ratios(conn)
    conn.close()

    total = len(latest)

    # Quality screen: ROE > 15% AND D/E < 1
    quality = latest[
        (latest["return_on_equity_pct"] > 15)
        & (latest["debt_to_equity"] < 1)
        & (latest["return_on_equity_pct"].notna())
    ]

    # Debt-free screen: D/E == 0
    debt_free = latest[latest["debt_to_equity"] == 0]

    # High-growth screen: revenue CAGR > 15%
    high_growth = latest[latest["revenue_cagr_5yr"] > 15]

    print(f"Companies with latest-year ratios: {total}")
    print()
    print(f"Quality screen (ROE > 15% AND D/E < 1): {len(quality)} companies")
    print(f"  expected 15-50: {'PASS' if 15 <= len(quality) <= 50 else 'CHECK'}")
    print(f"Debt-free (D/E = 0): {len(debt_free)} companies")
    print(f"High-growth (rev CAGR > 15%): {len(high_growth)} companies")
    print()
    print("Sample of Quality screen results:")
    cols = [
        "company_id",
        "year",
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
    ]
    print(quality[cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
