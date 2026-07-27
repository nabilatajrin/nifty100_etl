"""Peer comparison endpoints (Sprint 6, Day 40)."""

from fastapi import APIRouter, HTTPException

from ..db import get_connection

router = APIRouter(tags=["peers"])


@router.get("/peers/{group_name}")
def peer_group(group_name: str):
    """All companies in a peer group with percentile rank for each of 10 metrics."""
    conn = get_connection()
    exists = conn.execute(
        "SELECT 1 FROM peer_percentiles WHERE peer_group_name = ? LIMIT 1",
        (group_name,),
    ).fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found")

    rows = conn.execute(
        "SELECT * FROM peer_percentiles WHERE peer_group_name = ?", (group_name,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/companies/{ticker}/peers/compare")
def peer_radar(ticker: str):
    """Radar data: 8-axis metric values for the company, its peer group average,
    and the benchmark company."""
    conn = get_connection()
    company_row = conn.execute(
        "SELECT peer_group_name FROM peer_percentiles WHERE company_id = ? LIMIT 1",
        (ticker,),
    ).fetchone()
    if not company_row:
        conn.close()
        raise HTTPException(status_code=404,
                            detail=f"No peer group assigned for '{ticker}'")

    group_name = company_row["peer_group_name"]
    group_rows = conn.execute(
        "SELECT metric, value FROM peer_percentiles WHERE company_id = ? AND peer_group_name = ?",
        (ticker, group_name),
    ).fetchall()
    company_values = {r["metric"]: r["value"] for r in group_rows}

    avg_rows = conn.execute(
        "SELECT metric, AVG(value) AS avg_value FROM peer_percentiles "
        "WHERE peer_group_name = ? GROUP BY metric",
        (group_name,),
    ).fetchall()
    peer_avg = {r["metric"]: r["avg_value"] for r in avg_rows}

    benchmark = None
    try:
        bench_row = conn.execute(
            "SELECT company_id FROM peer_groups WHERE peer_group_name = ? "
            "AND is_benchmark = 'TRUE' LIMIT 1",
            (group_name,),
        ).fetchone()
        benchmark = bench_row["company_id"] if bench_row else None
    except Exception:
        pass

    conn.close()
    return {
        "company_id": ticker,
        "peer_group_name": group_name,
        "company_values": company_values,
        "peer_group_average": peer_avg,
        "benchmark_company": benchmark,
    }
