"""API tests — companies endpoint (Sprint 6, Day 42)."""


def test_list_companies_returns_92(client):
    resp = client.get("/api/v1/companies")
    assert resp.status_code == 200
    assert len(resp.json()) == 92


def test_get_company_correct_data(client):
    resp = client.get("/api/v1/companies/CO0")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "CO0"
    assert body["company_name"] == "Company 0"


def test_get_invalid_company_returns_404(client):
    resp = client.get("/api/v1/companies/INVALID")
    assert resp.status_code == 404
