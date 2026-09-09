from mock_salesforce.db import get_connection, init_db
from mock_salesforce.seed import seed_if_empty


def test_seed_if_empty_seeds_opportunities_across_ten_stages(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    conn = get_connection()
    init_db(conn)
    seed_if_empty(conn)
    accounts = conn.execute("SELECT id FROM accounts").fetchall()
    opps = conn.execute("SELECT * FROM opportunities").fetchall()
    conn.close()

    # Every named account has an opportunity. The unelaborated rest of the book does not,
    # which is ordinary: most accounts are not in play in any given year.
    named = conn_named_ids()
    opp_account_ids = {o["account_id"] for o in opps}
    assert named.issubset(opp_account_ids)
    assert len({a["id"] for a in accounts}) > len(opp_account_ids)

    stages = {o["stage_name"] for o in opps}
    assert len(stages) >= 5
    assert "Closed Won" in stages
    assert "Closed Lost" in stages

    for o in opps:
        expect_closed = o["stage_name"] in ("Closed Won", "Closed Lost")
        assert bool(o["is_closed"]) == expect_closed
        assert bool(o["is_won"]) == (o["stage_name"] == "Closed Won")


def conn_named_ids():
    """Ids of the ten accounts named in canon, which are the ones that carry detail."""
    from mock_salesforce.db import get_connection
    conn = get_connection()
    rows = conn.execute(
        "SELECT id FROM accounts WHERE external_id IN "
        "('ACCOUNT-1001','ACCOUNT-1002','ACCOUNT-1003','ACCOUNT-1004','ACCOUNT-1005',"
        " 'ACCOUNT-1006','ACCOUNT-1007','ACCOUNT-1008','ACCOUNT-1009','ACCOUNT-1010')"
    ).fetchall()
    conn.close()
    return {r["id"] for r in rows}
