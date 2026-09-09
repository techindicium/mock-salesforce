def test_create_lead_success(client):
    resp = client.post("/leads", json={"last_name": "Doe", "company": "Acme Corp"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["last_name"] == "Doe"
    assert body["company"] == "Acme Corp"
    assert body["status"] == "New"
    assert body["converted"] is False
    assert body["converted_at"] is None
    assert body["id"] is not None


def test_create_lead_missing_last_name(client):
    resp = client.post("/leads", json={"company": "Acme Corp"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_create_lead_missing_company(client):
    resp = client.post("/leads", json={"last_name": "Doe"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_create_lead_invalid_status(client):
    resp = client.post(
        "/leads", json={"last_name": "Doe", "company": "Acme", "status": "Bogus"}
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_create_lead_invalid_rating(client):
    resp = client.post(
        "/leads", json={"last_name": "Doe", "company": "Acme", "rating": "Bogus"}
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_list_leads_ordered_by_created_at(client):
    client.post("/leads", json={"last_name": "First", "company": "Acme"})
    client.post("/leads", json={"last_name": "Second", "company": "Acme"})
    resp = client.get("/leads")
    assert resp.status_code == 200
    names = [row["last_name"] for row in resp.json() if row["last_name"] in ("First", "Second")]
    assert names == ["First", "Second"]


def test_list_leads_filters_by_status(client):
    client.post("/leads", json={"last_name": "A", "company": "Acme", "status": "New"})
    client.post("/leads", json={"last_name": "B", "company": "Acme", "status": "Qualified"})
    resp = client.get("/leads", params={"status": "Qualified"})
    assert resp.status_code == 200
    assert all(row["status"] == "Qualified" for row in resp.json())
    assert any(row["last_name"] == "B" for row in resp.json())


def test_list_leads_filters_by_converted(client):
    created = client.post("/leads", json={"last_name": "Conv", "company": "Acme"}).json()
    client.post(f"/leads/{created['id']}/convert", json={})
    resp = client.get("/leads", params={"converted": "true"})
    assert resp.status_code == 200
    assert any(row["id"] == created["id"] for row in resp.json())
    resp = client.get("/leads", params={"converted": "false"})
    assert all(row["id"] != created["id"] for row in resp.json())


def test_get_lead_by_id_success(client):
    created = client.post("/leads", json={"last_name": "Doe", "company": "Acme"}).json()
    resp = client.get(f"/leads/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["last_name"] == "Doe"


def test_get_lead_by_id_not_found(client):
    resp = client.get("/leads/999999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "LEAD_NOT_FOUND"


def test_patch_lead_updates_fields(client):
    created = client.post("/leads", json={"last_name": "Doe", "company": "Acme"}).json()
    resp = client.patch(f"/leads/{created['id']}", json={"status": "Contacted"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "Contacted"
    assert body["updated_at"] != created["updated_at"]


def test_patch_lead_ignores_converted_fields(client):
    created = client.post("/leads", json={"last_name": "Doe", "company": "Acme"}).json()
    resp = client.patch(
        f"/leads/{created['id']}",
        json={"converted_account_id": 999999, "company": "Updated Co"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["converted_account_id"] is None
    assert body["company"] == "Updated Co"


def test_patch_lead_invalid_status(client):
    created = client.post("/leads", json={"last_name": "Doe", "company": "Acme"}).json()
    resp = client.patch(f"/leads/{created['id']}", json={"status": "Bogus"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_patch_converted_lead_returns_409(client):
    created = client.post("/leads", json={"last_name": "Doe", "company": "Acme"}).json()
    client.post(f"/leads/{created['id']}/convert", json={})
    resp = client.patch(f"/leads/{created['id']}", json={"status": "Contacted"})
    assert resp.status_code == 409
    assert resp.json()["error"] == "LEAD_ALREADY_CONVERTED"


def test_delete_lead_success(client):
    created = client.post("/leads", json={"last_name": "Doe", "company": "Acme"}).json()
    resp = client.delete(f"/leads/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/leads/{created['id']}").status_code == 404


def test_delete_converted_lead_returns_409(client):
    created = client.post("/leads", json={"last_name": "Doe", "company": "Acme"}).json()
    client.post(f"/leads/{created['id']}/convert", json={})
    resp = client.delete(f"/leads/{created['id']}")
    assert resp.status_code == 409
    assert resp.json()["error"] == "LEAD_ALREADY_CONVERTED"
    assert client.get(f"/leads/{created['id']}").status_code == 200


def test_convert_lead_creates_new_account_and_contact(client):
    created = client.post(
        "/leads",
        json={
            "first_name": "Jane", "last_name": "Doe", "company": "Acme Corp",
            "email": "jane@acme.com",
        },
    ).json()
    resp = client.post(f"/leads/{created['id']}/convert", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["converted"] is True
    assert body["converted_at"] is not None
    assert body["converted_account_id"] is not None
    assert body["converted_contact_id"] is not None
    assert body["converted_opportunity_id"] is None

    account = client.get(f"/accounts/{body['converted_account_id']}").json()
    assert account["name"] == "Acme Corp"
    contact = client.get(f"/contacts/{body['converted_contact_id']}").json()
    assert contact["first_name"] == "Jane"
    assert contact["last_name"] == "Doe"
    assert contact["account_id"] == body["converted_account_id"]


def test_convert_lead_attaches_to_existing_account_and_contact(client):
    account = client.post("/accounts", json={"name": "Existing Co"}).json()
    contact = client.post(
        "/contacts", json={"account_id": account["id"], "last_name": "Smith"}
    ).json()
    lead = client.post("/leads", json={"last_name": "Doe", "company": "Existing Co"}).json()

    resp = client.post(
        f"/leads/{lead['id']}/convert",
        json={"account_id": account["id"], "contact_id": contact["id"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["converted_account_id"] == account["id"]
    assert body["converted_contact_id"] == contact["id"]
    # No new contact was created under the account.
    assert len(client.get("/contacts", params={"account_id": account["id"]}).json()) == 1


def test_convert_lead_unknown_account_id_returns_404(client):
    lead = client.post("/leads", json={"last_name": "Doe", "company": "Acme"}).json()
    resp = client.post(f"/leads/{lead['id']}/convert", json={"account_id": 999999})
    assert resp.status_code == 404
    assert resp.json()["error"] == "LEAD_CONVERT_ACCOUNT_NOT_FOUND"


def test_convert_lead_unknown_contact_id_returns_404(client):
    account = client.post("/accounts", json={"name": "Existing Co"}).json()
    lead = client.post("/leads", json={"last_name": "Doe", "company": "Existing Co"}).json()
    resp = client.post(
        f"/leads/{lead['id']}/convert",
        json={"account_id": account["id"], "contact_id": 999999},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "LEAD_CONVERT_CONTACT_NOT_FOUND"


def test_convert_lead_contact_account_mismatch_returns_422(client):
    account_a = client.post("/accounts", json={"name": "A Co"}).json()
    account_b = client.post("/accounts", json={"name": "B Co"}).json()
    contact_b = client.post(
        "/contacts", json={"account_id": account_b["id"], "last_name": "Smith"}
    ).json()
    lead = client.post("/leads", json={"last_name": "Doe", "company": "A Co"}).json()

    resp = client.post(
        f"/leads/{lead['id']}/convert",
        json={"account_id": account_a["id"], "contact_id": contact_b["id"]},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "LEAD_CONVERT_CONTACT_ACCOUNT_MISMATCH"


def test_convert_lead_with_create_opportunity(client):
    lead = client.post(
        "/leads", json={"last_name": "Doe", "company": "Acme Corp"}
    ).json()
    resp = client.post(
        f"/leads/{lead['id']}/convert",
        json={
            "create_opportunity": True,
            "opportunity_name": "Acme Corp - New Business",
            "opportunity_close_date": "2027-01-01",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["converted_opportunity_id"] is not None
    opportunity = client.get(f"/opportunities/{body['converted_opportunity_id']}").json()
    assert opportunity["name"] == "Acme Corp - New Business"
    assert opportunity["stage_name"] == "Prospecting"
    assert opportunity["account_id"] == body["converted_account_id"]


def test_convert_lead_create_opportunity_without_close_date_returns_422(client):
    lead = client.post("/leads", json={"last_name": "Doe", "company": "Acme"}).json()
    resp = client.post(
        f"/leads/{lead['id']}/convert", json={"create_opportunity": True}
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_convert_already_converted_lead_returns_409(client):
    lead = client.post("/leads", json={"last_name": "Doe", "company": "Acme"}).json()
    client.post(f"/leads/{lead['id']}/convert", json={})
    resp = client.post(f"/leads/{lead['id']}/convert", json={})
    assert resp.status_code == 409
    assert resp.json()["error"] == "LEAD_ALREADY_CONVERTED"


def test_convert_lead_unknown_id_returns_404(client):
    resp = client.post("/leads/999999/convert", json={})
    assert resp.status_code == 404
    assert resp.json()["error"] == "LEAD_NOT_FOUND"
