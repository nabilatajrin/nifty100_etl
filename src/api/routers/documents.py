"""Documents endpoint (Sprint 6, Day 40)."""

from fastapi import APIRouter, HTTPException

from ..db import get_connection

router = APIRouter(tags=["documents"])


@router.get("/companies/{ticker}/documents")
def company_documents(ticker: str):
    """Annual report links with an is_url_valid flag for each."""
    conn = get_connection()
    exists = conn.execute("SELECT 1 FROM companies WHERE id = ?", (ticker,)).fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    rows = conn.execute(
        "SELECT * FROM documents WHERE company_id = ? ORDER BY Year DESC",
        (ticker,),
    ).fetchall()
    conn.close()

    out = []
    for r in rows:
        d = dict(r)
        url = d.get("Annual_Report")
        # basic validity check without making a network call per-request
        d["is_url_valid"] = bool(url and isinstance(url, str) and url.startswith("http"))
        out.append(d)
    return out
