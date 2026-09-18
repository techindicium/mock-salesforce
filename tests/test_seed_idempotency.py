from fastapi.testclient import TestClient


def test_fresh_startup_seeds_accounts_via_http(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "startup.db"))
    from mock_salesforce.app import app

    with TestClient(app) as client:
        resp = client.get("/accounts")
        assert resp.status_code == 200
        assert len(resp.json()) == 10


def test_restart_against_seeded_database_does_not_duplicate(tmp_path, monkeypatch):
    db_path = str(tmp_path / "restart.db")
    monkeypatch.setenv("DB_PATH", db_path)
    from mock_salesforce.app import app

    with TestClient(app) as client:
        assert len(client.get("/accounts").json()) == 10
        # SEED_CONTACTS is a fully deterministic, statically-known list of exactly 8
        # entries — assert the exact count so a duplication regression on restart is
        # actually caught (a >= check would silently tolerate 16 contacts after restart).
        assert len(client.get("/contacts").json()) == 8
        assert len(client.get("/opportunities").json()) == 10
        assert len(client.get("/leads").json()) == 5

    # Second startup against the same DB_PATH — a fresh TestClient re-runs on_startup.
    with TestClient(app) as client:
        assert len(client.get("/accounts").json()) == 10
        assert len(client.get("/contacts").json()) == 8
        assert len(client.get("/opportunities").json()) == 10
        assert len(client.get("/leads").json()) == 5
