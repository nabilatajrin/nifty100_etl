"""Radar / polar charts — company vs peer group average (Sprint 3, Day 19).

8 axes: ROE, ROCE, NPM, D/E (inverted score), FCF score, PAT CAGR 5yr,
Revenue CAGR 5yr, Composite Score.
Each chart shows the company as a filled polygon and the peer group average
as a dashed outline overlay. Exported as PNG to reports/radar_charts/.
Companies with no peer group get a single-metric standalone chart vs the
Nifty 100 average instead.

Run:  python -m src.reports.radar_charts
"""

import os
import re
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dotenv import load_dotenv

from ..screener.composite_score import scale_0_100

AXES = [
    ("return_on_equity_pct", "ROE", False),
    (
        "return_on_capital_employed_pct",
        "ROCE",
        False,
    ),  # may be absent; handled gracefully
    ("net_profit_margin_pct", "NPM", False),
    ("debt_to_equity", "D/E (inv)", True),
    ("free_cash_flow_cr", "FCF", False),
    ("pat_cagr_5yr", "PAT CAGR 5yr", False),
    ("revenue_cagr_5yr", "Revenue CAGR 5yr", False),
    ("composite_quality_score", "Composite Score", False),
]


def _safe_filename(company_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", company_id)


def build_scored_frame(fr: pd.DataFrame) -> pd.DataFrame:
    """Scale every radar-axis metric to 0-100 (winsorised) so axes are comparable."""
    out = fr[["company_id"]].copy()
    for col, label, invert in AXES:
        if col in fr.columns:
            out[col] = scale_0_100(fr[col], invert=invert)
        else:
            out[col] = np.nan
    return out


def plot_radar(
    company_id: str,
    company_vals: list,
    peer_avg: list,
    labels: list,
    out_path: Path,
    group_name: str = None,
):
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    company_vals = company_vals + company_vals[:1]
    peer_avg = peer_avg + peer_avg[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, company_vals, color="#2E75B6", linewidth=2)
    ax.fill(angles, company_vals, color="#2E75B6", alpha=0.25, label=company_id)
    ax.plot(
        angles,
        peer_avg,
        color="#C00000",
        linewidth=1.5,
        linestyle="--",
        label="Peer group avg" if group_name else "Nifty 100 avg",
    )

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=7)

    title = f"{company_id}" + (
        f" vs {group_name}" if group_name else " vs Nifty 100 avg"
    )
    ax.set_title(title, fontsize=12, weight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=8)

    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)

    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    fr = fr.sort_values("year").groupby("company_id").tail(1).reset_index(drop=True)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    fr = fr.merge(sectors, on="company_id", how="left")

    peers = pd.read_sql("SELECT * FROM peer_groups", conn)
    group_col = next(
        (c for c in peers.columns if "group" in c.lower() and "name" in c.lower()), None
    )
    if group_col is None:
        group_col = next(
            (c for c in peers.columns if "peer" in c.lower() and c != "company_id"),
            None,
        )
    peers = peers.rename(columns={group_col: "peer_group_name"})[
        ["company_id", "peer_group_name"]
    ]
    conn.close()

    # composite score must exist for the last axis
    if "composite_quality_score" not in fr.columns:
        from ..screener.composite_score import composite_score

        fr["composite_quality_score"] = composite_score(fr)

    scored = build_scored_frame(fr)
    scored = scored.merge(peers, on="company_id", how="left")

    labels = [lbl for _, lbl, _ in AXES]
    cols = [col for col, _, _ in AXES]
    nifty_avg = scored[cols].mean().fillna(0).tolist()

    out_dir = Path("reports/radar_charts")
    out_dir.mkdir(parents=True, exist_ok=True)

    n_with_group, n_without = 0, 0
    for _, row in scored.iterrows():
        cid = row["company_id"]
        group = row["peer_group_name"]
        company_vals = [float(row[c]) if pd.notna(row[c]) else 0.0 for c in cols]

        if pd.notna(group):
            peer_rows = scored[scored["peer_group_name"] == group]
            peer_avg = peer_rows[cols].mean().fillna(0).tolist()
            n_with_group += 1
            group_label = group
        else:
            peer_avg = nifty_avg
            n_without += 1
            group_label = None

        out_path = out_dir / f"{_safe_filename(cid)}_radar.png"
        plot_radar(cid, company_vals, peer_avg, labels, out_path, group_label)

    print(f"Radar charts generated: {n_with_group + n_without}")
    print(f"  with peer group overlay: {n_with_group}")
    print(f"  standalone vs Nifty 100 avg: {n_without}")
    print(f"  saved to {out_dir}/")


if __name__ == "__main__":
    main()
