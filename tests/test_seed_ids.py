import re
import sqlite3

import pytest

from mock_salesforce.db import get_connection, get_db_path, init_db
from mock_salesforce.seed import SeedDataError, seed_if_empty

RESERVED_ID_PATTERN = re.compile(
    r"^(P|ACCOUNT|POLICY|INCIDENT|TICKET|INTERACTION|PROPOSAL|ARTICLE|OPPORTUNITY|EXPERIMENT"
    r"|HELDOUT)-"
)


def test_seeded_ids_never_match_canon_reserved_schemes(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    conn = get_connection()
    init_db(conn)
    seed_if_empty(conn)
    for table in ("accounts", "contacts", "opportunities", "leads"):
        for row in conn.execute(f"SELECT id FROM {table}").fetchall():
            assert not RESERVED_ID_PATTERN.match(str(row["id"]))
    conn.close()


def test_seed_module_never_reads_outside_this_repository():
    # Guards the "no runtime file read outside this repository" acceptance criterion as an
    # automated gate rather than review-by-inspection.
    import mock_salesforce.seed as seed_module

    source = open(seed_module.__file__).read()
    assert "course-shared" not in source
    assert "open(" not in source


def test_seed_data_invalid_names_the_offending_row(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    conn = get_connection()
    init_db(conn)
    bad_accounts = [
        {"name": "Bad Account", "account_type": "NotARealType",
         "industry": "Logistics and Supply Chain", "billing_country": "United States"}
    ]
    with pytest.raises(SeedDataError) as exc_info:
        seed_if_empty(conn, accounts=bad_accounts)
    assert exc_info.value.code == "SEED_DATA_INVALID"
    assert "Bad Account" in exc_info.value.message  # names the offending row, per spec
    conn.close()


def test_seed_db_not_writable_names_the_path(tmp_path, monkeypatch):
    db_path = str(tmp_path / "seed.db")
    monkeypatch.setenv("DB_PATH", db_path)
    conn = get_connection()
    init_db(conn)
    conn.close()

    class _BoomOnCommit(sqlite3.Connection):
        def commit(self):
            raise sqlite3.OperationalError("attempt to write a readonly database")

    boom_conn = sqlite3.connect(get_db_path(), factory=_BoomOnCommit)
    boom_conn.row_factory = sqlite3.Row
    with pytest.raises(SeedDataError) as exc_info:
        seed_if_empty(boom_conn)
    assert exc_info.value.code == "SEED_DB_NOT_WRITABLE"
    assert db_path in exc_info.value.message  # names the path, per spec
    boom_conn.close()
