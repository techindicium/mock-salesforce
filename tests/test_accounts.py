def test_create_account_success(client):
    resp = client.post("/accounts", json={"name": "Acme Corp", "account_type": "Customer"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Acme Corp"
    assert body["id"] is not None
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


def test_create_account_missing_name(client):
    resp = client.post("/accounts", json={"account_type": "Customer"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_create_account_invalid_account_type(client):
    resp = client.post("/accounts", json={"name": "Acme", "account_type": "Bogus"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_create_account_malformed_json(client):
    resp = client.post(
        "/accounts",
        content=b"{not valid json",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "MALFORMED_JSON"
