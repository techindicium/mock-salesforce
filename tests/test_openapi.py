def test_openapi_lists_all_mounted_routes(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200

    doc = response.json()
    paths = doc["paths"]

    assert "/health" in paths
    assert "get" in paths["/health"]

    for path in ("/accounts", "/contacts", "/opportunities"):
        assert path in paths
        assert "get" in paths[path]
        assert "post" in paths[path]

    for path in ("/accounts/{account_id}", "/contacts/{contact_id}", "/opportunities/{opportunity_id}"):
        assert path in paths

    # the static-serving catch-all is infrastructure, not a documented API route
    assert "/{full_path}" not in paths
