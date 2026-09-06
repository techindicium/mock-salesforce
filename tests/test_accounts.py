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


def test_list_accounts_ordered_by_created_at(client):
    client.post("/accounts", json={"name": "First"})
    client.post("/accounts", json={"name": "Second"})
    resp = client.get("/accounts")
    assert resp.status_code == 200
    names = [a["name"] for a in resp.json()]
    assert names == ["First", "Second"]


def test_get_account_by_id_success(client):
    created = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.get(f"/accounts/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Acme"


def test_get_account_by_id_not_found(client):
    resp = client.get("/accounts/999999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "ACCOUNT_NOT_FOUND"


def test_patch_account_updates_fields(client):
    created = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.patch(f"/accounts/{created['id']}", json={"industry": "Logistics"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["industry"] == "Logistics"
    assert body["updated_at"] != created["updated_at"]


def test_patch_account_ignores_id_and_created_at(client):
    created = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.patch(
        f"/accounts/{created['id']}",
        json={"id": 999999, "created_at": "2000-01-01T00:00:00Z", "name": "Updated"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["created_at"] == created["created_at"]
    assert body["name"] == "Updated"


def test_patch_account_invalid_account_type(client):
    created = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.patch(f"/accounts/{created['id']}", json={"account_type": "Bogus"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"
