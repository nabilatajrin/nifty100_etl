"""Screener endpoint (Sprint 6, Day 40)."""

from fastapi import APIRouter, HTTPException, Query

from ..db import get_connection

router = APIRouter(tags=["screener"])


@router.get("/screener")
def screener(
    min_roe: float = Query(None),
    max_de: float = Query(None),
    min_fcf: float = Query(None),
    sector: str = Query(None),
    min_rev_cagr_5yr: float = Query(None),
    min_pat_cagr_5yr: float = Query(None),
    max_pe: float = Query(None),
):
    """Filter companies by threshold parameters. Returns a ranked list."""
    # basic sanity validation -> HTTP 400 on clearly invalid values
    for name, val in [
        ("min_roe", min_roe),
        ("max_de", max_de),
        ("min_fcf", min_fcf),
        ("min_rev_cagr_5yr", min_rev_cagr_5yr),
        ("min_pat_cagr_5yr", min_pat_cagr_5yr),
        ("max_pe", max_pe),
    ]:
        if val is not None and (val != val):  # NaN check
            raise HTTPException(status_code=400, detail=f"Invalid value for {name}")
    if max_de is not None and max_de < 0:
        raise HTTPException(status_code=400, detail="max_de cannot be negative")
    if max_pe is not None and max_pe < 0:
        raise HTTPException(status_code=400, detail="max_pe cannot be negative")

    conn = get_connection()
    sql = """
        SELECT fr.company_id, c.company_name, s.broad_sector,
               fr.return_on_equity_pct, fr.debt_to_equity, fr.free_cash_flow_cr,
               fr.revenue_cagr_5yr, fr.pat_cagr_5yr
        FROM financial_ratios fr
        JOIN companies c ON c.id = fr.company_id
        LEFT JOIN sectors s ON s.company_id = fr.company_id
        WHERE fr.year = (SELECT MAX(year) FROM financial_ratios fr2
                         WHERE fr2.company_id = fr.company_id)
    """
    params = []
    if min_roe is not None:
        sql += " AND fr.return_on_equity_pct >= ?"
        params.append(min_roe)
    if max_de is not None:
        sql += " AND (fr.debt_to_equity <= ? OR s.broad_sector = 'Financials')"
        params.append(max_de)
    if min_fcf is not None:
        sql += " AND fr.free_cash_flow_cr >= ?"
        params.append(min_fcf)
    if sector:
        sql += " AND s.broad_sector = ?"
        params.append(sector)
    if min_rev_cagr_5yr is not None:
        sql += " AND fr.revenue_cagr_5yr >= ?"
        params.append(min_rev_cagr_5yr)
    if min_pat_cagr_5yr is not None:
        sql += " AND fr.pat_cagr_5yr >= ?"
        params.append(min_pat_cagr_5yr)

    sql += " ORDER BY fr.return_on_equity_pct DESC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]
