from mock_salesforce.db import get_connection, init_db
from mock_salesforce.seed import SEED_ACCOUNTS, seed_if_empty

EXPECTED_NAMES = {
    "Marchetti Construction", "Ferreira Padarias", "Hollis Veterinary Group",
    "Atlantic Marine Supplies", "Cafe Nordeste", "Vaz e Filhos Transportes",
    "Clinica Dental Aurora", "Bright Path Tutoring", "Studio Lumen",
    "Oliveira Serralharia",
}


def test_seed_if_empty_seeds_the_ten_named_accounts(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    conn = get_connection()
    init_db(conn)
    seed_if_empty(conn)
    rows = conn.execute("SELECT * FROM accounts").fetchall()
    conn.close()
    assert len(rows) == 10
    assert {r["name"] for r in rows} == EXPECTED_NAMES
    for row in rows:
        assert row["industry"]  # every account records what the customer does
        assert row["billing_country"]  # non-empty, no placeholder
        assert row["billing_country"] not in ("TBD", "Lorem", "")


def test_seed_accounts_fallback_constant_has_the_ten_named_with_valid_countries():
    # SEED_ACCOUNTS is the in-module fallback used when the generated fixture is absent. It
    # carries the ten named accounts only; the full book lives in the fixture.
    assert len(SEED_ACCOUNTS) == 10
    eu_countries = {"Portugal", "Germany", "Sweden", "Netherlands", "Denmark"}
    na_countries = {"United States"}
    latam_countries = {"Brazil", "Mexico", "Peru"}
    real_countries = eu_countries | na_countries | latam_countries
    for row in SEED_ACCOUNTS:
        assert row["billing_country"] in real_countries
