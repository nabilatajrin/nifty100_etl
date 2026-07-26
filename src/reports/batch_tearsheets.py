"""Batch tearsheet generation for all 92 companies (Sprint 5, Day 34).

Skips companies with fewer than 3 years of P&L history, logging them to
output/skipped_tearsheets.csv rather than crashing or silently omitting them.

Run:  python -m src.reports.batch_tearsheets
"""

import os
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from .tearsheet import build_tearsheet

MIN_YEARS = 3


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)

    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))

    pros_cons_path = Path("output/pros_cons_generated.csv")
    pc_all = pd.read_csv(pros_cons_path) if pros_cons_path.exists() else pd.DataFrame()

    cap_path = Path("output/capital_allocation.csv")
    cap_all = pd.read_csv(cap_path) if cap_path.exists() else pd.DataFrame()

    out_dir = Path("reports/tearsheets")
    out_dir.mkdir(parents=True, exist_ok=True)

    generated, skipped = [], []

    for _, row in companies.iterrows():
        ticker, name = row["id"], row["company_name"]

        pl_h = pd.read_sql("SELECT * FROM profitandloss WHERE company_id=? ORDER BY year",
                          conn, params=(ticker,))
        if len(pl_h) < MIN_YEARS:
            skipped.append({"company_id": ticker, "years_available": len(pl_h),
                            "reason": f"fewer than {MIN_YEARS} years of P&L data"})
            continue

        ratio_h = pd.read_sql("SELECT * FROM financial_ratios WHERE company_id=? ORDER BY year",
                             conn, params=(ticker,))
        bs_h = pd.read_sql("SELECT * FROM balancesheet WHERE company_id=? ORDER BY year",
                          conn, params=(ticker,))
        cf_h = pd.read_sql("SELECT * FROM cashflow WHERE company_id=? ORDER BY year",
                          conn, params=(ticker,))

        pros, cons = [], []
        if not pc_all.empty:
            pros = pc_all[(pc_all.company_id == ticker) & (pc_all.type == "pro")]["text"].tolist()
            cons = pc_all[(pc_all.company_id == ticker) & (pc_all.type == "con")]["text"].tolist()

        capital_label = None
        if not cap_all.empty:
            crow = cap_all[cap_all.company_id == ticker].sort_values("year").tail(1)
            if not crow.empty:
                capital_label = crow.iloc[0]["pattern_label"]

        out_path = out_dir / f"{ticker}_tearsheet.pdf"
        try:
            build_tearsheet(ticker, name, sector_map.get(ticker), ratio_h, pl_h, bs_h,
                            cf_h, pros, cons, capital_label, str(out_path))
            generated.append(ticker)
        except Exception as e:
            skipped.append({"company_id": ticker, "years_available": len(pl_h),
                            "reason": f"generation error: {e}"})

    conn.close()

    skipped_df = pd.DataFrame(skipped, columns=["company_id", "years_available", "reason"])
    Path("output").mkdir(exist_ok=True)
    skipped_df.to_csv("output/skipped_tearsheets.csv", index=False)

    print(f"Generated: {len(generated)} tearsheets")
    print(f"Skipped: {len(skipped_df)} companies (see output/skipped_tearsheets.csv)")
    if not skipped_df.empty:
        print(skipped_df.to_string(index=False))

    # verify file count and minimum size
    pdfs = list(out_dir.glob("*.pdf"))
    undersized = [p.name for p in pdfs if p.stat().st_size < 30 * 1024]
    print(f"\nTotal PDF files on disk: {len(pdfs)}")
    if undersized:
        print(f"WARNING — under 30KB: {undersized}")
    else:
        print("All tearsheets are >= 30 KB.")


if __name__ == "__main__":
    main()
