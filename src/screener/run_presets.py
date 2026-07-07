"""Run the 6 preset screeners against the full 92-company universe (Sprint 3, Day 16).

Loads the latest-year financial_ratios row per company, runs each preset from
screener_config.yaml, and reports how many companies pass — verifying each
returns between 5 and 50 (the sprint exit criterion).

Run:  python -m src.screener.run_presets
"""

import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

from .engine import load_config, run_preset

PRESETS = [
    "quality_compounder",
    "value_pick",
    "growth_accelerator",
    "dividend_champion",
    "debt_free_bluechip",
    "turnaround_watch",
]


def latest_ratios(conn) -> pd.DataFrame:
    """Latest-year financial_ratios row per company, joined with sales & net_profit."""
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    fr = fr.sort_values("year").groupby("company_id").tail(1).reset_index(drop=True)

    # bring in sales & net_profit (for sales/net_profit presets) from P&L latest year
    pl = pd.read_sql("SELECT company_id, year, sales, net_profit FROM profitandloss", conn)
    pl = pl.sort_values("year").groupby("company_id").tail(1)
    pl = pl.rename(columns={"sales": "sales_cr", "net_profit": "net_profit_cr"})
    fr = fr.merge(pl[["company_id", "sales_cr", "net_profit_cr"]],
                  on="company_id", how="left")

    # bring in valuation columns (P/E, P/B, dividend yield, market cap) from market_cap
    try:
        mc = pd.read_sql(
            "SELECT company_id, year, pe_ratio, pb_ratio, "
            "dividend_yield_pct, market_cap_crore FROM market_cap", conn)
        mc = mc.sort_values("year").groupby("company_id").tail(1)
        fr = fr.merge(
            mc[["company_id", "pe_ratio", "pb_ratio",
                "dividend_yield_pct", "market_cap_crore"]],
            on="company_id", how="left")
    except Exception:
        pass  # market_cap table may be absent in some builds
    return fr


def main() -> None:
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)

    df = latest_ratios(conn)
    sectors_df = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()

    # ensure a composite score column exists so the engine can sort
    if "composite_quality_score" not in df.columns:
        # simple stand-in until Day 17 builds the real weighted score
        df["composite_quality_score"] = df["return_on_equity_pct"].fillna(0)

    sectors = df["company_id"].map(
        dict(zip(sectors_df["company_id"], sectors_df["broad_sector"]))
    )
    sectors.index = df.index

    config = load_config()

    print(f"Universe: {len(df)} companies\n")
    print(f"{'Preset':<22}{'Passes':>8}   Status")
    print("-" * 45)
    all_ok = True
    for name in PRESETS:
        result = run_preset(df, name, config, sectors)
        n = len(result)
        ok = 5 <= n <= 50
        all_ok &= ok
        print(f"{name:<22}{n:>8}   {'PASS' if ok else 'CHECK (want 5-50)'}")

    print("\n" + ("All presets in range ✓" if all_ok
                  else "Some presets out of range — see CHECK rows above."))

    # show a sample from Quality Compounder
    qc = run_preset(df, "quality_compounder", config, sectors)
    print("\nQuality Compounder — top 8:")
    cols = [c for c in ["company_id", "return_on_equity_pct", "debt_to_equity",
                        "revenue_cagr_5yr"] if c in qc.columns]
    print(qc[cols].head(8).to_string(index=False))


if __name__ == "__main__":
    main()
