"""Valuation module — FCF yield, sector P/E benchmarking, over/undervaluation flags
(Sprint 4, Day 26).

Uses market_cap.xlsx (already loaded into the market_cap table) plus
financial_ratios for FCF. Flags:
  P/E > sector_median * 1.5  -> "Caution"
  P/E < sector_median * 0.7  -> "Discount"
  otherwise                  -> "Fair"

Run:  python -m src.analytics.valuation
"""

import os
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv


def load_data(conn) -> pd.DataFrame:
    """Latest-year market_cap joined with sector and latest FCF."""
    mc = pd.read_sql("SELECT * FROM market_cap", conn)
    mc_latest = (
        mc.sort_values("year").groupby("company_id").tail(1).reset_index(drop=True)
    )

    companies = pd.read_sql(
        "SELECT id AS company_id, company_name FROM companies", conn
    )
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)

    fr = pd.read_sql(
        "SELECT company_id, year, free_cash_flow_cr FROM financial_ratios", conn
    )
    fr = (
        fr.sort_values("year")
        .groupby("company_id")
        .tail(1)[["company_id", "free_cash_flow_cr"]]
    )

    df = mc_latest.merge(companies, on="company_id", how="left")
    df = df.merge(sectors, on="company_id", how="left")
    df = df.merge(fr, on="company_id", how="left")
    return df, mc


def compute_5yr_median_pe(mc_all_years: pd.DataFrame) -> pd.Series:
    """Each company's own trailing 5-year median P/E (own valuation history)."""
    recent = mc_all_years.sort_values("year").groupby("company_id").tail(5)
    return recent.groupby("company_id")["pe_ratio"].median()


def compute_fcf_yield(df: pd.DataFrame) -> pd.Series:
    """FCF / market_cap_crore * 100. None if market_cap missing/zero."""
    mcap = pd.to_numeric(df["market_cap_crore"], errors="coerce")
    fcf = pd.to_numeric(df["free_cash_flow_cr"], errors="coerce")
    yield_pct = fcf / mcap.replace(0, pd.NA) * 100
    return yield_pct


def compute_sector_median_pe(df: pd.DataFrame) -> pd.Series:
    """Sector median P/E in the latest year, broadcast back to each row."""
    pe = pd.to_numeric(df["pe_ratio"], errors="coerce")
    sector_median = df.assign(_pe=pe).groupby("broad_sector")["_pe"].transform("median")
    return sector_median


def apply_valuation_flag(pe: pd.Series, sector_median: pd.Series) -> pd.Series:
    """Caution / Discount / Fair, per the spec's thresholds. None PE -> 'N/A'."""
    flags = []
    for p, med in zip(pe, sector_median):
        if pd.isna(p) or pd.isna(med) or med == 0:
            flags.append("N/A")
        elif p > med * 1.5:
            flags.append("Caution")
        elif p < med * 0.7:
            flags.append("Discount")
        else:
            flags.append("Fair")
    return pd.Series(flags, index=pe.index)


def build_valuation_summary(conn) -> pd.DataFrame:
    df, mc_all_years = load_data(conn)

    df["FCF_yield_pct"] = compute_fcf_yield(df)

    sector_median_pe = compute_sector_median_pe(df)  # for the flag logic only
    own_5yr_median_pe = compute_5yr_median_pe(mc_all_years)
    df = df.merge(
        own_5yr_median_pe.rename("5yr_median_PE"), on="company_id", how="left"
    )

    df["PE_vs_sector_median_pct"] = (
        (pd.to_numeric(df["pe_ratio"], errors="coerce") - sector_median_pe)
        / sector_median_pe.replace(0, pd.NA)
        * 100
    )
    df["flag"] = apply_valuation_flag(df["pe_ratio"], sector_median_pe)

    out = df.rename(
        columns={
            "broad_sector": "sector",
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
        }
    )
    cols = [
        "company_id",
        "company_name",
        "sector",
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]
    return out[[c for c in cols if c in out.columns]]


def main() -> None:
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)
    summary = build_valuation_summary(conn)
    conn.close()

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    summary.to_excel(out_dir / "valuation_summary.xlsx", index=False)
    flagged = summary[summary["flag"].isin(["Caution", "Discount"])]
    flagged.to_csv(out_dir / "valuation_flags.csv", index=False)

    print(f"valuation_summary.xlsx: {len(summary)} rows")
    print(f"valuation_flags.csv: {len(flagged)} rows")
    print(f"  Caution: {(summary['flag'] == 'Caution').sum()}")
    print(f"  Discount: {(summary['flag'] == 'Discount').sum()}")
    print(f"  Fair: {(summary['flag'] == 'Fair').sum()}")
    print(f"  N/A: {(summary['flag'] == 'N/A').sum()}")


if __name__ == "__main__":
    main()
