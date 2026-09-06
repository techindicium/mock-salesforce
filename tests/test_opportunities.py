def test_create_opportunity_defaults_to_prospecting(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Big Deal", "close_date": "2026-12-01"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["stage_name"] == "Prospecting"
    assert body["is_closed"] is False
    assert body["is_won"] is False
    assert body["account_id"] == account["id"]
    assert body["id"] is not None


def test_create_opportunity_unknown_account(client):
    resp = client.post(
        "/opportunities",
        json={"account_id": 999999, "name": "Big Deal", "close_date": "2026-12-01"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "OPPORTUNITY_ACCOUNT_NOT_FOUND"
    assert client.get("/opportunities").json() == []


def test_create_opportunity_missing_required_fields(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    base = {"account_id": account["id"], "name": "Big Deal", "close_date": "2026-12-01"}
    for missing_field in ("name", "account_id", "close_date"):
        payload = {k: v for k, v in base.items() if k != missing_field}
        resp = client.post("/opportunities", json=payload)
        assert resp.status_code == 422
        assert resp.json()["error"] == "VALIDATION_ERROR"


def test_create_opportunity_invalid_stage_name(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.post(
        "/opportunities",
        json={
            "account_id": account["id"],
            "name": "Big Deal",
            "close_date": "2026-12-01",
            "stage_name": "Bogus Stage",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"
