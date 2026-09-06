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

    account_ids = {a["id"] for a in accounts}
    opp_account_ids = {o["account_id"] for o in opps}
    assert account_ids.issubset(opp_account_ids)  # at least one Opportunity per Account

    stages = {o["stage_name"] for o in opps}
    assert len(stages) >= 5
    assert "Closed Won" in stages
    assert "Closed Lost" in stages

    for o in opps:
        expect_closed = o["stage_name"] in ("Closed Won", "Closed Lost")
        assert bool(o["is_closed"]) == expect_closed
        assert bool(o["is_won"]) == (o["stage_name"] == "Closed Won")
