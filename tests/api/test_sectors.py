"""API tests — sectors endpoint (Sprint 6, Day 42)."""


def test_sectors_returns_exactly_11(client):
    resp = client.get("/api/v1/sectors")
    assert resp.status_code == 200
    assert len(resp.json()) == 11


def test_sector_companies_only_it(client):
    resp = client.get("/api/v1/sectors/IT/companies")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 9  # matches the 9 IT companies in the test fixture
    ids = [r["company_id"] for r in results]
    assert all(c.startswith("CO") for c in ids)


def test_unknown_sector_returns_404(client):
    resp = client.get("/api/v1/sectors/FAKESECTOR/companies")
    assert resp.status_code == 404
