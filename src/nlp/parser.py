"""NLP analysis text parser (Sprint 5, Day 29).

Parses text fields in analysis.xlsx like "10 Years: 21%" into structured
(period_years, value_pct) pairs using regex, cross-validates against the
Ratio Engine's computed CAGR, and logs anything that fails to parse.

Run:  python -m src.nlp.parser
"""

import os
import re
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

PATTERN = re.compile(r"(\d+)\s*Years?:?\s*([\d.]+)%")

TARGET_FIELDS = {
    "compounded_sales_growth": "revenue_cagr",
    "compounded_profit_growth": "pat_cagr",
    "stock_price_cagr": "stock_price_cagr",
    "roe": "roe",
}

# maps our metric_type -> the computed CAGR column to cross-validate against
# (only revenue/pat have a direct Ratio Engine equivalent at a fixed window)
CROSS_VALIDATE_AGAINST = {
    "revenue_cagr": "revenue_cagr_5yr",
    "pat_cagr": "pat_cagr_5yr",
}


def parse_field(raw_text) -> tuple:
    """Return (period_years, value_pct) or (None, None) if it doesn't match."""
    if pd.isna(raw_text):
        return None, None
    m = PATTERN.search(str(raw_text))
    if not m:
        return None, None
    period = int(m.group(1))
    value = float(m.group(2))
    return period, value


def parse_analysis(analysis_df: pd.DataFrame) -> tuple:
    """Returns (parsed_df, failures_df)."""
    parsed_rows = []
    failure_rows = []

    for _, row in analysis_df.iterrows():
        cid = row.get("company_id")
        for field, metric_type in TARGET_FIELDS.items():
            if field not in analysis_df.columns:
                continue
            raw = row.get(field)
            if pd.isna(raw):
                continue
            period, value = parse_field(raw)
            if period is None:
                failure_rows.append(
                    {
                        "company_id": cid,
                        "field": field,
                        "raw_text": raw,
                    }
                )
            else:
                parsed_rows.append(
                    {
                        "company_id": cid,
                        "metric_type": metric_type,
                        "period_years": period,
                        "value_pct": value,
                    }
                )

    parsed = pd.DataFrame(
        parsed_rows, columns=["company_id", "metric_type", "period_years", "value_pct"]
    )
    failures = pd.DataFrame(failure_rows, columns=["company_id", "field", "raw_text"])
    return parsed, failures


def cross_validate(
    parsed: pd.DataFrame, computed_ratios: pd.DataFrame, tolerance: float = 5.0
) -> pd.DataFrame:
    """Flag rows where |parsed - computed| > tolerance percentage points."""
    flags = []
    latest = (
        computed_ratios.sort_values("year")
        .groupby("company_id")
        .tail(1)
        .set_index("company_id")
    )

    for metric_type, computed_col in CROSS_VALIDATE_AGAINST.items():
        if computed_col not in latest.columns:
            continue
        sub = parsed[parsed["metric_type"] == metric_type]
        for _, r in sub.iterrows():
            cid = r["company_id"]
            if cid not in latest.index:
                continue
            computed_val = latest.loc[cid, computed_col]
            if pd.isna(computed_val):
                continue
            diff = abs(r["value_pct"] - computed_val)
            if diff > tolerance:
                flags.append(
                    {
                        "company_id": cid,
                        "metric_type": metric_type,
                        "parsed_value": r["value_pct"],
                        "computed_value": round(computed_val, 2),
                        "diff": round(diff, 2),
                    }
                )
    return pd.DataFrame(flags)


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)
    analysis = pd.read_sql("SELECT * FROM analysis", conn)
    ratios = pd.read_sql(
        "SELECT company_id, year, revenue_cagr_5yr, pat_cagr_5yr FROM financial_ratios",
        conn,
    )
    conn.close()

    parsed, failures = parse_analysis(analysis)
    divergent = cross_validate(parsed, ratios)

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    parsed.to_csv(out_dir / "analysis_parsed.csv", index=False)
    failures.to_csv(out_dir / "parse_failures.csv", index=False)

    print(f"analysis_parsed.csv: {len(parsed)} rows parsed")
    print(f"parse_failures.csv: {len(failures)} rows failed to parse")
    print(f"Cross-validation divergences (>5%): {len(divergent)}")
    if not divergent.empty:
        print(divergent.to_string(index=False))


if __name__ == "__main__":
    main()
