from mock_salesforce.db import get_connection, init_db
from mock_salesforce.seed import SEED_ACCOUNTS, seed_if_empty

EXPECTED_NAMES = {
    "Nordkai Logistics", "Tavares Distribuicao", "Halden Cold Chain",
    "Brightpath Freight", "Meseta Almacenes", "Kestrel Parts Group",
    "Vlietwerk BV", "Sunder Retail Supply", "Copal Andina", "Fjordline Depot",
}


def test_seed_if_empty_seeds_the_whole_book_including_the_ten_named(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    conn = get_connection()
    init_db(conn)
    seed_if_empty(conn)
    rows = conn.execute("SELECT * FROM accounts").fetchall()
    conn.close()
    assert len(rows) == 412  # the whole book; ten of them are named in canon
    assert EXPECTED_NAMES.issubset({r["name"] for r in rows})
    for row in rows:
        assert row["industry"] == "Logistics and Supply Chain"
        assert row["billing_country"]  # non-empty, no placeholder
        assert row["billing_country"] not in ("TBD", "Lorem", "")


def test_seed_accounts_fallback_constant_has_the_ten_named_with_valid_countries():
    # SEED_ACCOUNTS is the in-module fallback used when the generated fixture is absent. It
    # carries the ten named accounts only; the full book lives in the fixture.
    assert len(SEED_ACCOUNTS) == 10
    eu_countries = {"Germany", "Sweden", "Netherlands", "Denmark"}
    na_countries = {"United States"}
    latam_countries = {"Brazil", "Mexico", "Peru"}
    real_countries = eu_countries | na_countries | latam_countries
    for row in SEED_ACCOUNTS:
        assert row["billing_country"] in real_countries
