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


def test_deal_js_is_served_and_fetches_opportunity_account_and_contacts(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/js/deal.js")
        assert response.status_code == 200
        js = response.text
        assert "fetchOpportunity" in js
        assert "fetchAccount" in js
        assert "fetchContacts" in js
        assert "from './error-state.js'" in js
        assert "from './errors.js'" in js


def test_deal_js_wires_edit_and_delete_opportunity(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/deal.html").text
        assert 'id="edit-opportunity-form"' in html
        assert 'id="delete-opportunity-btn"' in html

        js = client.get("/js/deal.js").text
        assert "updateOpportunity" in js
        assert "deleteOpportunity" in js
        assert "inlineErrorMessage" in js
        assert "confirm(" in js


def test_deal_js_wires_contact_crud_and_list_refresh(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/deal.html").text
        assert 'id="contact-form"' in html
        assert 'id="new-contact-btn"' in html

        js = client.get("/js/deal.js").text
        assert "createContact" in js
        assert "updateContact" in js
        assert "deleteContact" in js
        assert "from './list-state.js'" in js
        assert "replaceList" in js


def test_deal_page_links_to_accounts_page(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/deal.html").text
        assert 'href="accounts.html"' in html


def test_deal_html_has_sidebar_with_three_nav_items(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/deal.html").text

    assert 'class="sidebar"' in html
    assert html.count('class="nav-item') == 3
    assert html.count('class="nav-item active"') == 1
