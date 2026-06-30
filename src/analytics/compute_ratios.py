"""Populate the financial_ratios table for all companies (Sprint 2, Day 12).

Reads the cleaned core tables from nifty100.db, computes every KPI per
company-year using the analytics modules, and writes:
  - financial_ratios table (recomputed)
  - output/capital_allocation.csv
Run:  python -m src.analytics.compute_ratios
"""

from pathlib import Path
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

from . import ratios as R
from . import cagr as C
from . import cashflow_kpis as CF


def _series_for(df: pd.DataFrame, company_id: str, col: str) -> list:
    """Chronological list of `col` for a company (oldest -> newest)."""
    sub = df[df["company_id"] == company_id].sort_values("year")
    return sub[col].tolist()


def compute_all(db_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    conn = sqlite3.connect(db_path)
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()

    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))

    # index BS and CF by (company_id, year) for fast lookup
    bs_idx = bs.set_index(["company_id", "year"]).to_dict("index")
    cf_idx = cf.set_index(["company_id", "year"]).to_dict("index")

    rows = []
    capital_rows = []

    for _, p in pl.iterrows():
        cid, yr = p["company_id"], p["year"]
        b = bs_idx.get((cid, yr), {})
        c = cf_idx.get((cid, yr), {})
        sector = sector_map.get(cid)

        sales = p.get("sales")
        net_profit = p.get("net_profit")
        op = p.get("operating_profit")
        dep = p.get("depreciation")
        eq = b.get("equity_capital")
        res = b.get("reserves")
        borr = b.get("borrowings")
        ta = b.get("total_assets")
        inv = b.get("investments")
        cfo = c.get("operating_activity")
        cfi = c.get("investing_activity")
        cff = c.get("financing_activity")

        npm = R.net_profit_margin(net_profit, sales)
        opm = R.operating_profit_margin(op, sales)
        roe = R.return_on_equity(net_profit, eq, res)
        de = R.debt_to_equity(borr, eq, res)
        icr = R.interest_coverage(op, p.get("other_income"), p.get("interest"))
        at = R.asset_turnover(sales, ta)
        fcf = CF.free_cash_flow(cfo, cfi) if (cfo is not None or cfi is not None) else None

        # CAGRs from the company's revenue / PAT / EPS series
        rev_series = _series_for(pl, cid, "sales")
        pat_series = _series_for(pl, cid, "net_profit")
        eps_series = _series_for(pl, cid, "eps")
        rev_cagr5, _ = C.cagr_from_series(rev_series, 5)
        pat_cagr5, _ = C.cagr_from_series(pat_series, 5)
        eps_cagr5, _ = C.cagr_from_series(eps_series, 5)

        rows.append({
            "company_id": cid, "year": yr,
            "net_profit_margin_pct": npm,
            "operating_profit_margin_pct": opm,
            "return_on_equity_pct": roe,
            "debt_to_equity": de,
            "interest_coverage": icr,
            "asset_turnover": at,
            "free_cash_flow_cr": fcf,
            "capex_cr": abs(cfi) if cfi is not None else None,
            "earnings_per_share": p.get("eps"),
            "book_value_per_share": None,  # computed in later sprint
            "dividend_payout_ratio_pct": p.get("dividend_payout"),
            "total_debt_cr": borr,
            "cash_from_operations_cr": cfo,
            "revenue_cagr_5yr": rev_cagr5,
            "pat_cagr_5yr": pat_cagr5,
            "eps_cagr_5yr": eps_cagr5,
        })

        if cfo is not None and cfi is not None and cff is not None:
            so, si, sf, label = CF.capital_allocation_pattern(cfo, cfi, cff)
            capital_rows.append({
                "company_id": cid, "year": yr,
                "cfo_sign": so, "cfi_sign": si, "cff_sign": sf,
                "pattern_label": label,
            })

    return pd.DataFrame(rows), pd.DataFrame(capital_rows)


def main() -> None:
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    ratios_df, capital_df = compute_all(db)

    # write financial_ratios table (replace)
    conn = sqlite3.connect(db)
    ratios_df.to_sql("financial_ratios", conn, if_exists="replace", index=False)
    n = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    conn.close()

    capital_df.to_csv(out_dir / "capital_allocation.csv", index=False)

    print(f"financial_ratios populated: {n} rows")
    print(f"capital_allocation.csv: {len(capital_df)} rows")
    print(f"  (need >= 1100 rows: {'PASS' if n >= 1100 else 'CHECK'})")


if __name__ == "__main__":
    main()
