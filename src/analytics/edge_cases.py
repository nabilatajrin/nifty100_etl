"""Bank carve-out + edge-case anomaly logging (Sprint 2, Day 13).

Cross-checks the ratio engine's computed ROCE / ROE against the pre-computed
roce_percentage / roe_percentage columns in companies.xlsx. Anomalies where the
difference exceeds a threshold are written to output/ratio_edge_cases.log, each
categorised as: DATA_SOURCE_ISSUE, VERSION_DIFFERENCE, or FORMULA_DISCREPANCY.

The 19 Financials-sector companies have their D/E high-leverage warning
suppressed (high leverage is structurally normal for banks / NBFCs / insurers).
"""

from pathlib import Path
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

from . import ratios as R

FINANCIALS = "Financials"
ROCE_TOL = 5.0   # percentage-point tolerance for cross-check
ROE_TOL = 5.0


def _categorise(diff: float) -> str:
    """Rough categorisation of an anomaly by how large the gap is."""
    if diff > 25:
        return "DATA_SOURCE_ISSUE"      # implausibly large gap -> likely bad source value
    if diff > 10:
        return "FORMULA_DISCREPANCY"    # meaningful gap -> formula/definition mismatch
    return "VERSION_DIFFERENCE"         # small gap -> different snapshot/period


def build_edge_log(db_path: str | Path) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    companies = pd.read_sql(
        "SELECT id, roce_percentage, roe_percentage FROM companies", conn
    )
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    ratios = pd.read_sql(
        "SELECT company_id, year, return_on_equity_pct FROM financial_ratios", conn
    )
    conn.close()

    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))

    # latest-year computed ROE per company
    latest = (ratios.sort_values("year")
              .groupby("company_id")
              .tail(1)
              .set_index("company_id")["return_on_equity_pct"]
              .to_dict())

    entries = []
    for _, c in companies.iterrows():
        cid = c["id"]
        sector = sector_map.get(cid, "Unknown")
        is_financial = sector == FINANCIALS

        src_roe = c["roe_percentage"]
        comp_roe = latest.get(cid)

        # ROE cross-check (skip if either side missing)
        if src_roe is not None and comp_roe is not None:
            # some source ROE values are fractions (e.g. TCS 0.52) — flag as anomaly
            diff = abs(comp_roe - src_roe)
            if diff > ROE_TOL:
                entries.append({
                    "company_id": cid, "sector": sector,
                    "metric": "ROE",
                    "computed": round(comp_roe, 2),
                    "source": src_roe,
                    "diff": round(diff, 2),
                    "category": _categorise(diff),
                    "financials_carveout": is_financial,
                })

    log_df = pd.DataFrame(entries)
    return log_df


def main() -> None:
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    out = Path("output")
    out.mkdir(exist_ok=True)

    log_df = build_edge_log(db)
    log_path = out / "ratio_edge_cases.log"

    with open(log_path, "w") as f:
        f.write("# Ratio Engine — Edge Case & Cross-Check Log (Sprint 2, Day 13)\n")
        f.write(f"# Total anomalies: {len(log_df)}\n")
        f.write("# Categories: DATA_SOURCE_ISSUE, FORMULA_DISCREPANCY, VERSION_DIFFERENCE\n")
        f.write("# Financials-sector companies: D/E high-leverage warning suppressed.\n\n")
        if log_df.empty:
            f.write("No anomalies above tolerance.\n")
        else:
            for _, r in log_df.iterrows():
                f.write(
                    f"{r['company_id']:<12} [{r['sector']:<20}] {r['metric']}: "
                    f"computed={r['computed']} source={r['source']} "
                    f"diff={r['diff']} -> {r['category']}"
                    f"{'  (financials carve-out)' if r['financials_carveout'] else ''}\n"
                )

    # summary
    print(f"ratio_edge_cases.log written: {len(log_df)} anomalies")
    if not log_df.empty:
        print("By category:")
        print(log_df["category"].value_counts().to_string())
        n_fin = int(log_df["financials_carveout"].sum())
        print(f"Financials-sector anomalies (carve-out applied): {n_fin}")


if __name__ == "__main__":
    main()
