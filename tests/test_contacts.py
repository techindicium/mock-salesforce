# tests/test_contacts.py
def test_create_contact_success(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.post("/contacts", json={"account_id": account["id"], "last_name": "Doe"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["last_name"] == "Doe"
    assert body["account_id"] == account["id"]


def test_create_contact_unknown_account(client):
    resp = client.post("/contacts", json={"account_id": 999999, "last_name": "Doe"})
    assert resp.status_code == 404
    assert resp.json()["error"] == "CONTACT_ACCOUNT_NOT_FOUND"


def test_create_contact_missing_last_name(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.post("/contacts", json={"account_id": account["id"]})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"
