def test_serves_index_html_when_build_present(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html><body>crm-ui</body></html>")
    (static_dir / "app.js").write_text("console.log('hi');")
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(static_dir))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        root = client.get("/")
        assert root.status_code == 200
        assert "crm-ui" in root.text

        asset = client.get("/app.js")
        assert asset.status_code == 200
        assert "javascript" in asset.headers["content-type"]


def test_static_assets_are_served_with_no_store_cache_control(tmp_path, monkeypatch):
    # Regression guard: without this, browsers apply heuristic caching and can
    # silently keep serving a stale HTML/JS file after a rebuild/restart, which
    # looks indistinguishable from a real functional bug to whoever is testing it.
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html><body>crm-ui</body></html>")
    (static_dir / "app.js").write_text("console.log('hi');")
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(static_dir))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        assert client.get("/").headers["cache-control"] == "no-store"
        assert client.get("/app.js").headers["cache-control"] == "no-store"


def test_returns_404_when_build_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(tmp_path / "does-not-exist"))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 404
        assert response.json()["error"] == "STATIC_ASSET_NOT_FOUND"


def test_returns_404_for_path_traversal_attempt(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html><body>crm-ui</body></html>")
    secret = tmp_path / "secret.txt"
    secret.write_text("outside the static root")
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(static_dir))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        # A literal "/../secret.txt" gets dot-segment-normalized away by the HTTP client
        # itself (httpx resolves it to "/secret.txt" before the request is even sent), so
        # it would never reach the traversal guard. Percent-encoding the slash (%2F)
        # prevents that client-side normalization, so the literal string "../secret.txt"
        # arrives as the full_path path-parameter value, which is what actually exercises
        # the `static_root not in target.parents` guard in `serve_static`.
        response = client.get("/..%2Fsecret.txt")
        assert response.status_code == 404
        assert response.json()["error"] == "STATIC_ASSET_NOT_FOUND"


def test_returns_404_for_null_byte_in_path(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html><body>crm-ui</body></html>")
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(static_dir))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        # A NUL byte is valid percent-encoding (%00) but makes Path.resolve() raise
        # ValueError: embedded null character in path. This must still surface as a
        # Salesforce-shaped 404, never a bare 500.
        response = client.get("/foo%00bar")
        assert response.status_code == 404
        assert response.json()["error"] == "STATIC_ASSET_NOT_FOUND"
