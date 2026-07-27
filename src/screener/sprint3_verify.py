"""Sprint 3 verification (Day 21).

1. Confirms Quality Compounder results all satisfy ROE > 15% and D/E < 1.
2. Confirms that within IT Services, the company with the highest ROE has
   the highest ROE percentile rank (the spec's explicit spot-check).
Run:  python -m src.screener.sprint3_verify
"""

import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

from .engine import load_config, run_preset
from .run_presets import latest_ratios
from .composite_score import composite_score


def verify_quality_compounder(db_path: str):
    conn = sqlite3.connect(db_path)
    df = latest_ratios(conn)
    sectors_df = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()

    df = df.merge(sectors_df, on="company_id", how="left")
    df["composite_quality_score"] = composite_score(df)
    sectors = df["broad_sector"]
    sectors.index = df.index

    config = load_config()
    result = run_preset(df, "quality_compounder", config, sectors)

    print("--- Quality Compounder spot-check ---")
    print(f"{len(result)} companies returned")
    bad = result[
        (result["return_on_equity_pct"] <= 15)
        | ((result["debt_to_equity"] >= 1) & (result["broad_sector"] != "Financials"))
    ]
    if bad.empty:
        print(
            "PASS: all results satisfy ROE > 15% and D/E < 1 (or Financials carve-out)"
        )
    else:
        print(f"CHECK: {len(bad)} rows violate the threshold logic")
        print(
            bad[["company_id", "return_on_equity_pct", "debt_to_equity"]].to_string(
                index=False
            )
        )

    print("\nTop 5:")
    print(
        result[
            [
                "company_id",
                "return_on_equity_pct",
                "debt_to_equity",
                "composite_quality_score",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


def verify_peer_ranking(
    db_path: str, group: str = "IT Services", metric: str = "return_on_equity_pct"
):
    conn = sqlite3.connect(db_path)
    pct = pd.read_sql(
        "SELECT * FROM peer_percentiles WHERE peer_group_name = ? AND metric = ?",
        conn,
        params=(group, metric),
    )
    conn.close()

    print(f"\n--- Peer ranking spot-check: {group}, {metric} ---")
    if pct.empty:
        print(f"CHECK: no data found for group '{group}'")
        return

    by_value = pct.sort_values("value", ascending=False)
    by_rank = pct.sort_values("percentile_rank", ascending=False)
    top_by_value = by_value.iloc[0]["company_id"]
    top_by_rank = by_rank.iloc[0]["company_id"]

    print(
        pct.sort_values("value", ascending=False)[
            ["company_id", "value", "percentile_rank"]
        ].to_string(index=False)
    )

    if top_by_value == top_by_rank:
        print(
            f"\nPASS: highest {metric} ({top_by_value}) has the highest percentile rank"
        )
    else:
        print(
            f"\nCHECK: highest value is {top_by_value} but highest rank is {top_by_rank}"
        )


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    verify_quality_compounder(db)
    verify_peer_ranking(db, "IT Services", "return_on_equity_pct")
    verify_peer_ranking(db, "FMCG", "return_on_equity_pct")


if __name__ == "__main__":
    main()
