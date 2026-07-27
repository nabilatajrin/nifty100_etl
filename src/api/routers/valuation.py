"""Valuation / market-cap endpoint (Sprint 6, Day 40)."""

from fastapi import APIRouter, HTTPException

from ..db import get_connection

router = APIRouter(tags=["valuation"])


@router.get("/market-cap/{ticker}")
def market_cap_history(ticker: str):
    """Historical valuation multiples (P/E, P/B, EV/EBITDA, dividend yield), 2019-2024."""
    conn = get_connection()
    exists = conn.execute("SELECT 1 FROM companies WHERE id = ?", (ticker,)).fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    try:
        rows = conn.execute(
            "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year",
            (ticker,),
        ).fetchall()
    except Exception:
        rows = []
    conn.close()
    return [dict(r) for r in rows]
