"""Health-check router (Sprint 6, Day 38)."""

import time

from fastapi import APIRouter

from ..db import get_connection, APP_VERSION, START_TIME

router = APIRouter(tags=["health"])

TABLES = [
    "companies", "profitandloss", "balancesheet", "cashflow", "analysis",
    "documents", "prosandcons", "sectors", "financial_ratios", "market_cap",
]


@router.get("/health")
def health():
    """Returns service status, per-table row counts, uptime, and version."""
    conn = get_connection()
    counts = {}
    for t in TABLES:
        try:
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception:
            counts[t] = None
    conn.close()

    return {
        "status": "ok",
        "db_row_counts": counts,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "version": APP_VERSION,
    }
