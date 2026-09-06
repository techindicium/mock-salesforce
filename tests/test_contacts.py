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


def test_list_contacts_filtered_by_account(client):
    a1 = client.post("/accounts", json={"name": "A1"}).json()
    a2 = client.post("/accounts", json={"name": "A2"}).json()
    client.post("/contacts", json={"account_id": a1["id"], "last_name": "One"})
    client.post("/contacts", json={"account_id": a2["id"], "last_name": "Two"})

    resp = client.get("/contacts", params={"account_id": a1["id"]})
    assert resp.status_code == 200
    names = [c["last_name"] for c in resp.json()]
    assert names == ["One"]

    resp_all = client.get("/contacts")
    assert len(resp_all.json()) == 2


def test_get_contact_by_id_success(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/contacts", json={"account_id": account["id"], "last_name": "Doe"}
    ).json()
    resp = client.get(f"/contacts/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["last_name"] == "Doe"


def test_get_contact_by_id_not_found(client):
    resp = client.get("/contacts/999999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "CONTACT_NOT_FOUND"
