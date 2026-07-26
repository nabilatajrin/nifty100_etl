"""Capital Allocation Report (Sprint 5, Day 32).

Verifies capital_allocation.csv (from Sprint 2 Day 12) is complete, prints a
distribution summary for the latest year, and detects year-over-year pattern
changes per company, saved to output/pattern_changes.csv.

Run:  python -m src.analytics.capital_allocation_report
"""

import os
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv


def load_capital_allocation(path: str = "output/capital_allocation.csv") -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"{path} not found — run Sprint 2 Day 12 (compute_ratios.py) first."
        )
    return pd.read_csv(p)


def verify_completeness(cap: pd.DataFrame, expected_companies: set) -> dict:
    present_companies = set(cap["company_id"].unique())
    missing = expected_companies - present_companies
    rows_per_company = cap.groupby("company_id").size()
    return {
        "total_rows": len(cap),
        "companies_present": len(present_companies),
        "companies_missing": sorted(missing),
        "min_years_per_company": int(rows_per_company.min()) if not rows_per_company.empty else 0,
        "max_years_per_company": int(rows_per_company.max()) if not rows_per_company.empty else 0,
    }


def latest_year_distribution(cap: pd.DataFrame) -> pd.Series:
    latest = cap.sort_values("year").groupby("company_id").tail(1)
    return latest["pattern_label"].value_counts()


def detect_pattern_changes(cap: pd.DataFrame) -> pd.DataFrame:
    """For each company, find every year where the pattern differs from the
    prior year. Returns company_id, year, prior_pattern, new_pattern."""
    changes = []
    for cid, grp in cap.sort_values("year").groupby("company_id"):
        labels = grp["pattern_label"].tolist()
        years = grp["year"].tolist()
        for i in range(1, len(labels)):
            if labels[i] != labels[i - 1]:
                changes.append({
                    "company_id": cid,
                    "year": years[i],
                    "prior_pattern": labels[i - 1],
                    "new_pattern": labels[i],
                })
    return pd.DataFrame(changes, columns=["company_id", "year", "prior_pattern", "new_pattern"])


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)
    all_companies = set(pd.read_sql("SELECT id FROM companies", conn)["id"])
    conn.close()

    cap = load_capital_allocation()

    report = verify_completeness(cap, all_companies)
    print("--- Completeness check ---")
    print(f"Total rows: {report['total_rows']}")
    print(f"Companies present: {report['companies_present']} / {len(all_companies)}")
    if report["companies_missing"]:
        print(f"MISSING companies: {report['companies_missing']}")
    else:
        print("All companies present.")
    print(f"Years per company: min={report['min_years_per_company']}, "
          f"max={report['max_years_per_company']}")

    print("\n--- Latest-year pattern distribution ---")
    dist = latest_year_distribution(cap)
    print(dist.to_string())

    changes = detect_pattern_changes(cap)
    out_path = Path("output/pattern_changes.csv")
    out_path.parent.mkdir(exist_ok=True)
    changes.to_csv(out_path, index=False)

    print(f"\npattern_changes.csv: {len(changes)} year-over-year changes detected")
    if not changes.empty:
        print(changes.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
