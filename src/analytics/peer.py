"""Peer percentile rankings (Sprint 3, Day 18).

Computes PERCENT_RANK for 10 metrics within each of the 11 peer groups and
populates the peer_percentiles table in SQLite.

D/E is inverted (1 - rank) so that a LOWER debt-to-equity gives a HIGHER
percentile. Companies not in any peer group are reported, not errored.

Run:  python -m src.analytics.peer
"""

import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

# metric column -> invert? (True means lower is better)
METRICS = {
    "return_on_equity_pct": False,
    "operating_profit_margin_pct": False,
    "net_profit_margin_pct": False,
    "debt_to_equity": True,  # inverted: lower D/E = better
    "free_cash_flow_cr": False,
    "pat_cagr_5yr": False,
    "revenue_cagr_5yr": False,
    "eps_cagr_5yr": False,
    "interest_coverage": False,
    "asset_turnover": False,
}


def load_data(conn):
    """Latest-year ratios joined to peer group membership."""
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    fr = fr.sort_values("year").groupby("company_id").tail(1).reset_index(drop=True)

    peers = pd.read_sql("SELECT * FROM peer_groups", conn)
    # the peer_groups table column names can vary; find the group-name column
    group_col = next(
        (c for c in peers.columns if "group" in c.lower() and "name" in c.lower()), None
    )
    if group_col is None:
        group_col = next(
            (c for c in peers.columns if "peer" in c.lower() and c != "company_id"),
            None,
        )
    peers = peers.rename(columns={group_col: "peer_group_name"})
    return fr, peers[["company_id", "peer_group_name"]]


def compute_percentiles(fr: pd.DataFrame, peers: pd.DataFrame) -> pd.DataFrame:
    """Long-format table: company_id, peer_group_name, metric, value, percentile_rank, year."""
    merged = fr.merge(peers, on="company_id", how="inner")

    rows = []
    for group_name, grp in merged.groupby("peer_group_name"):
        for metric, invert in METRICS.items():
            if metric not in grp.columns:
                continue
            values = pd.to_numeric(grp[metric], errors="coerce")
            # pandas rank(pct=True) is the PERCENT_RANK equivalent
            ranks = values.rank(pct=True, method="average")
            if invert:
                ranks = 1 - ranks
            for cid, val, rk, yr in zip(grp["company_id"], values, ranks, grp["year"]):
                if pd.isna(val):
                    continue
                rows.append(
                    {
                        "company_id": cid,
                        "peer_group_name": group_name,
                        "metric": metric,
                        "value": round(float(val), 4),
                        "percentile_rank": round(float(rk), 4),
                        "year": yr,
                    }
                )
    return pd.DataFrame(rows)


def unassigned_companies(fr: pd.DataFrame, peers: pd.DataFrame) -> list:
    """Companies with no peer group — reported, never raised as an error."""
    assigned = set(peers["company_id"])
    return sorted(set(fr["company_id"]) - assigned)


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)

    fr, peers = load_data(conn)
    pct = compute_percentiles(fr, peers)

    pct.to_sql("peer_percentiles", conn, if_exists="replace", index=False)
    n = conn.execute("SELECT COUNT(*) FROM peer_percentiles").fetchone()[0]
    groups = conn.execute(
        "SELECT COUNT(DISTINCT peer_group_name) FROM peer_percentiles"
    ).fetchone()[0]
    conn.close()

    print(f"peer_percentiles populated: {n} rows across {groups} peer groups")

    missing = unassigned_companies(fr, peers)
    print(f"Companies with no peer group assigned: {len(missing)}")
    if missing:
        print("  (no error raised — these are reported, per spec)")
        print(" ", ", ".join(missing[:12]) + (" ..." if len(missing) > 12 else ""))

    # spot-check: highest ROE in a group should have the highest ROE percentile
    if not pct.empty:
        sample_group = pct["peer_group_name"].iloc[0]
        roe = pct[
            (pct["peer_group_name"] == sample_group)
            & (pct["metric"] == "return_on_equity_pct")
        ]
        roe = roe.sort_values("value", ascending=False)
        print(f"\nSpot-check — {sample_group} by ROE:")
        print(
            roe[["company_id", "value", "percentile_rank"]]
            .head(5)
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()
