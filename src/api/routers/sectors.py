"""Sector endpoints (Sprint 6, Day 40)."""

from fastapi import APIRouter, HTTPException

from ..db import get_connection

router = APIRouter(tags=["sectors"])


@router.get("/sectors")
def list_sectors():
    """All sectors with company_count, median_roe, median_pe, median_de."""
    conn = get_connection()
    sectors = [
        r["broad_sector"]
        for r in conn.execute(
            "SELECT DISTINCT broad_sector FROM sectors WHERE broad_sector IS NOT NULL"
        )
    ]

    results = []
    for sector in sectors:
        row = conn.execute(
            """
            SELECT COUNT(DISTINCT s.company_id) AS company_count
            FROM sectors s WHERE s.broad_sector = ?
        """,
            (sector,),
        ).fetchone()

        med = conn.execute(
            """
            SELECT fr.return_on_equity_pct, fr.debt_to_equity
            FROM financial_ratios fr
            JOIN sectors s ON s.company_id = fr.company_id
            WHERE s.broad_sector = ?
              AND fr.year = (SELECT MAX(year) FROM financial_ratios fr2
                            WHERE fr2.company_id = fr.company_id)
        """,
            (sector,),
        ).fetchall()

        roes = sorted(
            r["return_on_equity_pct"]
            for r in med
            if r["return_on_equity_pct"] is not None
        )
        des = sorted(
            r["debt_to_equity"] for r in med if r["debt_to_equity"] is not None
        )

        try:
            mc = conn.execute(
                """
                SELECT mc.pe_ratio FROM market_cap mc
                JOIN sectors s ON s.company_id = mc.company_id
                WHERE s.broad_sector = ?
                  AND mc.year = (SELECT MAX(year) FROM market_cap mc2
                                WHERE mc2.company_id = mc.company_id)
            """,
                (sector,),
            ).fetchall()
            pes = sorted(r["pe_ratio"] for r in mc if r["pe_ratio"] is not None)
        except Exception:
            pes = []

        def _median(vals):
            n = len(vals)
            if n == 0:
                return None
            mid = n // 2
            return vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2

        results.append(
            {
                "broad_sector": sector,
                "company_count": row["company_count"],
                "median_roe": _median(roes),
                "median_pe": _median(pes),
                "median_de": _median(des),
            }
        )
    conn.close()
    return results


@router.get("/sectors/{sector}/companies")
def sector_companies(sector: str):
    """All companies in a sector with latest-year KPIs."""
    conn = get_connection()
    exists = conn.execute(
        "SELECT 1 FROM sectors WHERE broad_sector = ? LIMIT 1", (sector,)
    ).fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")

    rows = conn.execute(
        """
        SELECT fr.company_id, c.company_name, fr.return_on_equity_pct,
               fr.debt_to_equity, fr.revenue_cagr_5yr, fr.free_cash_flow_cr
        FROM financial_ratios fr
        JOIN sectors s ON s.company_id = fr.company_id
        JOIN companies c ON c.id = fr.company_id
        WHERE s.broad_sector = ?
          AND fr.year = (SELECT MAX(year) FROM financial_ratios fr2
                        WHERE fr2.company_id = fr.company_id)
    """,
        (sector,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
