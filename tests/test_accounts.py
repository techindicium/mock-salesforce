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
    # Filter to the accounts this test created — a fresh database may already contain
    # seeded fixture accounts (see seed.py), so assert this test's own ordering rather
    # than assuming the list is otherwise empty.
    names = [a["name"] for a in resp.json() if a["name"] in ("First", "Second")]
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


def test_delete_account_no_dependents(client):
    created = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.delete(f"/accounts/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/accounts/{created['id']}").status_code == 404


def test_delete_account_with_contact_returns_409(client):
    from mock_salesforce.db import get_connection

    account = client.post("/accounts", json={"name": "Acme"}).json()
    conn = get_connection()
    conn.execute(
        "INSERT INTO contacts (account_id, last_name, created_at, updated_at) "
        "VALUES (?, ?, datetime('now'), datetime('now'))",
        (account["id"], "Doe"),
    )
    conn.commit()
    conn.close()

    resp = client.delete(f"/accounts/{account['id']}")
    assert resp.status_code == 409
    assert resp.json()["error"] == "ACCOUNT_HAS_DEPENDENTS"
    assert client.get(f"/accounts/{account['id']}").status_code == 200
