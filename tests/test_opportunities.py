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
    # A fresh database may already contain seeded fixture opportunities (see seed.py),
    # so assert no NEW opportunity was created (delta against the baseline) rather than
    # assuming the list is otherwise empty.
    before = client.get("/opportunities").json()
    resp = client.post(
        "/opportunities",
        json={"account_id": 999999, "name": "Big Deal", "close_date": "2026-12-01"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "OPPORTUNITY_ACCOUNT_NOT_FOUND"
    assert client.get("/opportunities").json() == before


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


def test_list_opportunities_filters(client):
    a1 = client.post("/accounts", json={"name": "A1"}).json()
    a2 = client.post("/accounts", json={"name": "A2"}).json()
    client.post(
        "/opportunities",
        json={
            "account_id": a1["id"], "name": "Deal One", "close_date": "2026-12-01",
            "stage_name": "Qualification",
        },
    )
    client.post(
        "/opportunities",
        json={"account_id": a2["id"], "name": "Deal Two", "close_date": "2026-12-01"},
    )

    resp = client.get("/opportunities", params={"account_id": a1["id"]})
    assert resp.status_code == 200
    assert [o["name"] for o in resp.json()] == ["Deal One"]

    resp = client.get("/opportunities", params={"stage_name": "Qualification"})
    # A fresh database may already contain seeded fixture opportunities in this same
    # stage (see seed.py), so scope the check to this test's own accounts rather than
    # assuming this test's opportunity is the only "Qualification" row globally.
    own_qualification = [
        o["name"] for o in resp.json() if o["account_id"] in (a1["id"], a2["id"])
    ]
    assert own_qualification == ["Deal One"]

    resp_all = client.get("/opportunities")
    own_all = [o for o in resp_all.json() if o["account_id"] in (a1["id"], a2["id"])]
    assert len(own_all) == 2


def test_get_opportunity_by_id_success(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()
    resp = client.get(f"/opportunities/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Deal"


def test_get_opportunity_by_id_not_found(client):
    resp = client.get("/opportunities/999999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "OPPORTUNITY_NOT_FOUND"


def test_patch_opportunity_updates_fields(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()
    resp = client.patch(
        f"/opportunities/{created['id']}",
        json={"amount": 50000, "next_step": "Send proposal"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["amount"] == 50000
    assert body["next_step"] == "Send proposal"
    assert body["updated_at"] != created["updated_at"]


def test_patch_opportunity_stage_recomputes_is_closed_is_won(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()

    won = client.patch(f"/opportunities/{created['id']}", json={"stage_name": "Closed Won"})
    assert won.status_code == 200
    assert won.json()["is_closed"] is True
    assert won.json()["is_won"] is True

    lost = client.patch(f"/opportunities/{created['id']}", json={"stage_name": "Closed Lost"})
    assert lost.status_code == 200
    assert lost.json()["is_closed"] is True
    assert lost.json()["is_won"] is False


def test_patch_opportunity_ignores_immutable_fields(client):
    a1 = client.post("/accounts", json={"name": "A1"}).json()
    a2 = client.post("/accounts", json={"name": "A2"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": a1["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()
    resp = client.patch(
        f"/opportunities/{created['id']}",
        json={
            "id": 999999, "account_id": a2["id"], "is_closed": True, "is_won": True,
            "created_at": "2000-01-01T00:00:00Z", "name": "Updated",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["account_id"] == a1["id"]
    assert body["created_at"] == created["created_at"]
    assert body["is_closed"] is False
    assert body["is_won"] is False
    assert body["name"] == "Updated"


def test_patch_opportunity_invalid_stage_name(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()
    resp = client.patch(f"/opportunities/{created['id']}", json={"stage_name": "Bogus"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_delete_opportunity_success(client):
    # A fresh database may already contain seeded fixture opportunities (see seed.py),
    # so assert the list returns to its pre-test baseline rather than assuming it's
    # empty after deleting this test's own opportunity.
    before = client.get("/opportunities").json()
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()
    resp = client.delete(f"/opportunities/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/opportunities/{created['id']}").status_code == 404
    assert client.get("/opportunities").json() == before


def test_delete_opportunity_not_found(client):
    resp = client.delete("/opportunities/999999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "OPPORTUNITY_NOT_FOUND"
