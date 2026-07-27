"""Portfolio statistics endpoint (Sprint 6, Day 40)."""

from fastapi import APIRouter

from ..db import get_connection

router = APIRouter(tags=["portfolio"])

KPI_10 = [
    "return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
    "operating_profit_margin_pct", "debt_to_equity", "interest_coverage",
    "asset_turnover", "revenue_cagr_5yr", "pat_cagr_5yr", "free_cash_flow_cr",
]


def _percentile(sorted_vals: list, pct: float):
    if not sorted_vals:
        return None
    n = len(sorted_vals)
    idx = pct * (n - 1)
    lo, hi = int(idx), min(int(idx) + 1, n - 1)
    frac = idx - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


@router.get("/portfolio/stats")
def portfolio_stats():
    """P10-P90 percentile table for 10 core KPIs across all companies."""
    conn = get_connection()
    cols_available = [r["name"] for r in conn.execute("PRAGMA table_info(financial_ratios)")]
    metrics = [k for k in KPI_10 if k in cols_available]

    rows = conn.execute(
        f"SELECT company_id, year, {', '.join(metrics)} FROM financial_ratios"
    ).fetchall()
    conn.close()

    # latest year per company
    latest_by_company = {}
    for r in rows:
        cid = r["company_id"]
        if cid not in latest_by_company or r["year"] > latest_by_company[cid]["year"]:
            latest_by_company[cid] = r

    result = {}
    for metric in metrics:
        vals = sorted(r[metric] for r in latest_by_company.values() if r[metric] is not None)
        result[metric] = {
            "P10": _percentile(vals, 0.10),
            "P25": _percentile(vals, 0.25),
            "P50": _percentile(vals, 0.50),
            "P75": _percentile(vals, 0.75),
            "P90": _percentile(vals, 0.90),
        }
    return result
