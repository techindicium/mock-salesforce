from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_deal_html_has_the_detail_dom_contract(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/deal.html")
        assert response.status_code == 200
        html = response.text
        # These exact ids are the DOM contract a later task's deal.js binds against
        # (getElementById with no fallback) — asserting only "a heading exists
        # somewhere" would let this task pass without the hooks that task needs.
        assert 'id="opportunity-name"' in html
        assert 'id="opportunity-fields"' in html
        assert 'id="account-fields"' in html
        assert 'id="contacts-list"' in html
        assert 'id="error-banner"' in html
        assert 'type="module"' in html
        assert 'js/deal.js' in html
