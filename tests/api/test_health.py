"""API tests — health endpoint (Sprint 6, Day 42)."""


def test_health_returns_200_and_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_health_db_row_counts_has_all_tables(client):
    resp = client.get("/api/v1/health")
    counts = resp.json()["db_row_counts"]
    expected_tables = {
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "sectors",
        "financial_ratios",
        "market_cap",
    }
    assert expected_tables.issubset(counts.keys())
