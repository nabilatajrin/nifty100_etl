"""Day 6 — Data Quality Manual Review.

Pulls 5 random companies and shows their data across all time-series tables,
reports year coverage per company, and flags companies with < 5 years of history.
Run:  python -m src.etl.review
"""

from pathlib import Path
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

TIMESERIES = ["profitandloss", "balancesheet", "cashflow", "financial_ratios"]


def main() -> None:
    load_dotenv()
    db_path = Path(os.getenv("DB_PATH", "data/nifty100.db"))
    conn = sqlite3.connect(db_path)

    # ---- pick 5 random companies ----
    sample = pd.read_sql(
        "SELECT id, company_name FROM companies ORDER BY RANDOM() LIMIT 5", conn
    )
    print("=" * 60)
    print("MANUAL REVIEW — 5 RANDOM COMPANIES")
    print("=" * 60)

    for _, row in sample.iterrows():
        cid = row["id"]
        print(f"\n### {cid} — {row['company_name']}")
        for tbl in TIMESERIES:
            try:
                df = pd.read_sql(
                    f"SELECT year FROM {tbl} WHERE company_id = ? ORDER BY year",
                    conn, params=(cid,),
                )
                yrs = df["year"].tolist()
                span = f"{yrs[0]} → {yrs[-1]}" if yrs else "no data"
                print(f"  {tbl:<18} {len(yrs):>3} yrs  ({span})")
            except Exception as e:
                print(f"  {tbl:<18} error: {e}")

    # ---- coverage report: companies with < 5 years of P&L ----
    print("\n" + "=" * 60)
    print("COVERAGE CHECK — companies with < 5 years of P&L")
    print("=" * 60)
    cov = pd.read_sql(
        """SELECT company_id, COUNT(*) AS years
           FROM profitandloss GROUP BY company_id
           HAVING years < 5 ORDER BY years""",
        conn,
    )
    if cov.empty:
        print("All companies have >= 5 years of P&L. ✓")
    else:
        print(cov.to_string(index=False))
        print(f"\n{len(cov)} companies flagged with < 5 years.")

    # ---- overall coverage distribution ----
    print("\n" + "=" * 60)
    print("YEAR COVERAGE DISTRIBUTION (P&L)")
    print("=" * 60)
    dist = pd.read_sql(
        """SELECT years, COUNT(*) AS num_companies FROM (
               SELECT company_id, COUNT(*) AS years
               FROM profitandloss GROUP BY company_id
           ) GROUP BY years ORDER BY years""",
        conn,
    )
    print(dist.to_string(index=False))

    conn.close()


if __name__ == "__main__":
    main()
