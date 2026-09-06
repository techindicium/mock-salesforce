from mock_salesforce.db import get_connection, init_db
from mock_salesforce.seed import seed_if_empty


def test_seed_if_empty_seeds_named_people_as_contacts(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    conn = get_connection()
    init_db(conn)
    seed_if_empty(conn)
    contacts = conn.execute("SELECT * FROM contacts").fetchall()
    accounts = {r["id"]: r["name"] for r in conn.execute("SELECT * FROM accounts").fetchall()}
    conn.close()

    assert len(contacts) >= 6
    distinct_accounts = {c["account_id"] for c in contacts}
    assert len(distinct_accounts) >= 4
    assert distinct_accounts.issubset(accounts.keys())
    for c in contacts:
        assert c["last_name"]  # never an invented placeholder name
        assert c["title"]      # plausible title derived from canon role
