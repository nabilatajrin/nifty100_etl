"""Shared pytest fixtures for API tests (Sprint 6, Day 42)."""

import os
import sqlite3

import pandas as pd
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_db(tmp_path_factory):
    """Builds a small but complete test database and points DB_PATH at it."""
    db_path = tmp_path_factory.mktemp("data") / "test_nifty100.db"
    conn = sqlite3.connect(db_path)

    # 92 companies across 11 sectors, matching the real spec's scale
    sectors_list = (["IT"] * 9 + ["Financials"] * 19 + ["Energy"] * 15
                    + ["FMCG"] * 8 + ["Healthcare"] * 5 + ["Materials"] * 8
                    + ["Industrials"] * 9 + ["Consumer Discretionary"] * 12
                    + ["Communication Services"] * 2 + ["Real Estate"] * 3
                    + ["Conglomerates"] * 2)
    ids = [f"CO{i}" for i in range(len(sectors_list))]

    pd.DataFrame({"id": ids, "company_name": [f"Company {i}" for i in range(len(ids))],
                 "roe_percentage": [20.0] * len(ids), "roce_percentage": [18.0] * len(ids)}
                ).to_sql("companies", conn, index=False)
    pd.DataFrame({"company_id": ids, "broad_sector": sectors_list, "sub_sector": "x",
                 "market_cap_category": "Large Cap"}).to_sql("sectors", conn, index=False)

    fr = pd.DataFrame({
        "company_id": ids, "year": "2024-03",
        "return_on_equity_pct": [20.0 + (i % 10) for i in range(len(ids))],
        "debt_to_equity": [0.1 if s == "Financials" else 0.5 for s in sectors_list],
        "free_cash_flow_cr": [100.0] * len(ids),
        "revenue_cagr_5yr": [10.0] * len(ids),
        "pat_cagr_5yr": [8.0] * len(ids),
    })
    fr.to_sql("financial_ratios", conn, index=False)

    for t in ["profitandloss", "balancesheet", "cashflow"]:
        pd.DataFrame({"company_id": ids, "year": "2024-03"}).to_sql(t, conn, index=False)
    pd.DataFrame({"company_id": [], "year": []}).to_sql("analysis", conn, index=False)
    pd.DataFrame({"company_id": [], "Year": []}).to_sql("documents", conn, index=False)
    pd.DataFrame({"company_id": [], "pros": []}).to_sql("prosandcons", conn, index=False)
    pd.DataFrame({"company_id": [], "pe_ratio": []}).to_sql("market_cap", conn, index=False)

    conn.close()
    return str(db_path)


@pytest.fixture(scope="session")
def client(test_db):
    os.environ["DB_PATH"] = test_db
    from src.api.main import app
    return TestClient(app)
