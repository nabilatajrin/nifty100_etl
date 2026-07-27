"""Company data endpoints (Sprint 6, Day 39)."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from ..db import get_connection

router = APIRouter(tags=["companies"])


def _company_exists(conn, ticker: str) -> bool:
    row = conn.execute("SELECT 1 FROM companies WHERE id = ?", (ticker,)).fetchone()
    return row is not None


def _year_filter_clause(from_year, to_year) -> tuple:
    clauses, params = [], []
    if from_year:
        clauses.append("year >= ?")
        params.append(from_year)
    if to_year:
        clauses.append("year <= ?")
        params.append(to_year)
    return (" AND " + " AND ".join(clauses)) if clauses else "", params


@router.get("/companies")
def list_companies(sector: str = None, market_cap_category: str = None, search: str = None):
    """List all companies, with optional sector / market-cap / name-ticker search filters."""
    conn = get_connection()
    sql = """
        SELECT c.id, c.company_name, s.broad_sector, s.sub_sector,
               c.roe_percentage AS roe_pct, c.roce_percentage AS roce_pct,
               s.market_cap_category
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        WHERE 1=1
    """
    params = []
    if sector:
        sql += " AND s.broad_sector = ?"
        params.append(sector)
    if market_cap_category:
        sql += " AND s.market_cap_category = ?"
        params.append(market_cap_category)
    if search:
        sql += " AND (c.company_name LIKE ? OR c.id LIKE ?)"
        like = f"%{search}%"
        params += [like, like]

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/companies/{ticker}")
def get_company(ticker: str):
    """Full company profile: companies fields + latest-year KPIs + sector data."""
    conn = get_connection()
    if not _company_exists(conn, ticker):
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    comp = dict(conn.execute("SELECT * FROM companies WHERE id = ?", (ticker,)).fetchone())
    sector_row = conn.execute("SELECT * FROM sectors WHERE company_id = ?", (ticker,)).fetchone()
    latest_ratios = conn.execute(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    conn.close()

    return {
        **comp,
        "sector": dict(sector_row) if sector_row else None,
        "latest_ratios": dict(latest_ratios) if latest_ratios else None,
    }


def _history_endpoint(table: str, ticker: str, from_year, to_year):
    conn = get_connection()
    if not _company_exists(conn, ticker):
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    clause, params = _year_filter_clause(from_year, to_year)
    sql = f"SELECT * FROM {table} WHERE company_id = ?{clause} ORDER BY year"
    rows = conn.execute(sql, [ticker] + params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/companies/{ticker}/pl")
def get_pl(ticker: str, from_year: str = Query(None), to_year: str = Query(None)):
    """P&L history. from_year/to_year in YYYY-MM format."""
    return _history_endpoint("profitandloss", ticker, from_year, to_year)


@router.get("/companies/{ticker}/bs")
def get_bs(ticker: str, from_year: str = Query(None), to_year: str = Query(None)):
    """Balance sheet history. from_year/to_year in YYYY-MM format."""
    return _history_endpoint("balancesheet", ticker, from_year, to_year)


@router.get("/companies/{ticker}/cashflow")
def get_cashflow(ticker: str, from_year: str = Query(None), to_year: str = Query(None)):
    """Cash flow history. from_year/to_year in YYYY-MM format."""
    return _history_endpoint("cashflow", ticker, from_year, to_year)


@router.get("/companies/{ticker}/ratios")
def get_ratios(ticker: str, year: str = Query(None)):
    """All computed KPIs per year, or a single year if `year` is given."""
    conn = get_connection()
    if not _company_exists(conn, ticker):
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    if year:
        rows = conn.execute(
            "SELECT * FROM financial_ratios WHERE company_id = ? AND year = ?",
            (ticker, year),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year",
            (ticker,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/companies/{ticker}/tearsheet")
def get_tearsheet(ticker: str):
    """Returns the pre-generated tearsheet PDF as a binary download."""
    conn = get_connection()
    exists = _company_exists(conn, ticker)
    conn.close()
    if not exists:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    path = Path("reports/tearsheets") / f"{ticker}_tearsheet.pdf"
    if not path.exists():
        raise HTTPException(status_code=404,
                            detail=f"Tearsheet for '{ticker}' has not been generated")
    return FileResponse(str(path), media_type="application/pdf",
                        filename=f"{ticker}_tearsheet.pdf")
