"""Cash Flow Intelligence — company-wide runner (Sprint 5, Day 31).

Computes CFO quality, CapEx intensity, FCF CAGR, FCF conversion, distress and
deleveraging flags, and capital allocation label for every company, and
writes output/cashflow_intelligence.xlsx + output/distress_alerts.csv.

Run:  python -m src.analytics.cashflow_intelligence
"""

import os
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from .cashflow_kpis import (
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
    capital_allocation_pattern,
    distress_signal,
    deleveraging_flag,
)
from .cagr import cagr_from_series


def build_intelligence(conn) -> pd.DataFrame:
    cf = pd.read_sql("SELECT * FROM cashflow ORDER BY company_id, year", conn)
    pl = pd.read_sql(
        "SELECT company_id, year, net_profit, operating_profit, sales "
        "FROM profitandloss ORDER BY company_id, year",
        conn,
    )
    bs = pd.read_sql(
        "SELECT company_id, year, borrowings FROM balancesheet "
        "ORDER BY company_id, year",
        conn,
    )
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    fr = pd.read_sql(
        "SELECT company_id, year, free_cash_flow_cr FROM financial_ratios "
        "ORDER BY company_id, year",
        conn,
    )

    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))
    rows = []

    for cid, cf_h in cf.groupby("company_id"):
        pl_h = pl[pl["company_id"] == cid]
        bs_h = bs[bs["company_id"] == cid]
        fr_h = fr[fr["company_id"] == cid]

        # merge on year to align CFO/PAT for the quality-score average
        merged = cf_h.merge(
            pl_h[["year", "net_profit", "operating_profit", "sales"]],
            on="year",
            how="inner",
        )
        if merged.empty:
            continue

        cfo_vals = merged["operating_activity"].tail(5).tolist()
        pat_vals = merged["net_profit"].tail(5).tolist()
        cfo_score, cfo_label = cfo_quality_score(cfo_vals, pat_vals)

        latest = merged.iloc[-1]
        capex_val, capex_label = capex_intensity(
            latest["investing_activity"], latest["sales"]
        )

        fcf_series = fr_h["free_cash_flow_cr"].tolist()
        fcf_cagr5, _ = (
            cagr_from_series(fcf_series, 5) if len(fcf_series) >= 6 else (None, None)
        )

        fcf_latest = fr_h["free_cash_flow_cr"].iloc[-1] if not fr_h.empty else None
        fcf_conv = (
            fcf_conversion_rate(fcf_latest, latest["operating_profit"])
            if fcf_latest is not None
            else None
        )

        cfo_latest = latest["operating_activity"]
        cff_latest = latest["financing_activity"]
        distress = distress_signal(cfo_latest, cff_latest)

        borr_h = bs_h.sort_values("year")
        delever = False
        if len(borr_h) >= 2:
            delever = deleveraging_flag(
                cff_latest, borr_h["borrowings"].iloc[-1], borr_h["borrowings"].iloc[-2]
            )

        so, si, sf, pattern_label = capital_allocation_pattern(
            cfo_latest, latest["investing_activity"], cff_latest, cfo_score
        )

        rows.append(
            {
                "company_id": cid,
                "sector": sector_map.get(cid, ""),
                "cfo_quality_score": (
                    round(cfo_score, 3) if cfo_score is not None else None
                ),
                "cfo_quality_label": cfo_label,
                "capex_intensity_pct": (
                    round(capex_val, 2) if capex_val is not None else None
                ),
                "capex_label": capex_label,
                "fcf_cagr_5yr": round(fcf_cagr5, 2) if fcf_cagr5 is not None else None,
                "fcf_conversion_pct": (
                    round(fcf_conv, 2) if fcf_conv is not None else None
                ),
                "distress_flag": distress,
                "deleveraging_flag": delever,
                "capital_allocation_label": pattern_label,
                "_cfo_latest": cfo_latest,
                "_cff_latest": cff_latest,
                "_net_profit_latest": (
                    pl_h["net_profit"].iloc[-1] if not pl_h.empty else None
                ),
            }
        )

    return pd.DataFrame(rows)


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)
    intel = build_intelligence(conn)
    conn.close()

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    public_cols = [c for c in intel.columns if not c.startswith("_")]
    intel[public_cols].to_excel(out_dir / "cashflow_intelligence.xlsx", index=False)

    distress = intel[intel["distress_flag"]]
    distress_out = distress.rename(
        columns={
            "_cfo_latest": "cfo_latest",
            "_cff_latest": "cff_latest",
            "_net_profit_latest": "net_profit_latest",
        }
    )[["company_id", "sector", "cfo_latest", "cff_latest", "net_profit_latest"]]
    distress_out.to_csv(out_dir / "distress_alerts.csv", index=False)

    print(f"cashflow_intelligence.xlsx: {len(intel)} rows")
    print(f"distress_alerts.csv: {len(distress_out)} companies flagged")
    print(f"deleveraging flagged: {intel['deleveraging_flag'].sum()} companies")
    print(f"\nCFO quality distribution:\n{intel['cfo_quality_label'].value_counts()}")
    print(f"\nCapEx intensity distribution:\n{intel['capex_label'].value_counts()}")


if __name__ == "__main__":
    main()
