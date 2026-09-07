from mock_salesforce.db import get_connection, init_db


def test_init_db_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "schema.db"))
    conn = get_connection()
    init_db(conn)
    init_db(conn)  # second call must not raise
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {"accounts", "contacts"}.issubset(tables)
    conn.close()


def test_init_db_creates_opportunities_table(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "schema2.db"))
    conn = get_connection()
    init_db(conn)
    init_db(conn)  # second call must not raise
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "opportunities" in tables
    conn.close()
