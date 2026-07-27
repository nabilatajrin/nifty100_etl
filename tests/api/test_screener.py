"""API tests — screener endpoint (Sprint 6, Day 42)."""


def test_screener_min_roe_filters_correctly(client):
    resp = client.get("/api/v1/screener", params={"min_roe": 25})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0
    assert all(r["return_on_equity_pct"] >= 25 for r in results)


def test_screener_invalid_param_returns_400(client):
    # max_de negative is a clearly invalid threshold -> should 400
    resp = client.get("/api/v1/screener", params={"max_de": -5})
    assert resp.status_code == 400
