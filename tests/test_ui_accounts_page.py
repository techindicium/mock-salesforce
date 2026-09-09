from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_accounts_html_has_the_list_and_form_dom_contract(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/accounts.html")
        assert response.status_code == 200
        html = response.text
        assert 'id="accounts-list"' in html
        assert 'id="new-account-btn"' in html
        assert 'id="account-form"' in html
        assert 'id="error-banner"' in html
        assert 'type="module"' in html
        assert 'js/accounts.js' in html
        assert 'id="account-id-input"' in html
        assert 'id="account-form-error"' in html
        assert 'id="account-name-input"' in html
        assert 'id="account-industry-input"' in html
        assert 'id="account-phone-input"' in html
        assert 'id="cancel-account-form-btn"' in html


def test_accounts_js_wires_crud_and_409_dependents_handling(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/js/accounts.js")
        assert response.status_code == 200
        js = response.text
        assert "createAccount" in js
        assert "updateAccount" in js
        assert "deleteAccount" in js
        assert "from './list-state.js'" in js
        assert "from './form-errors.js'" in js
        assert "from './error-state.js'" in js
        assert "confirm(" in js


def test_accounts_js_wires_new_opportunity_and_contact_crud_per_account(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/accounts.html").text
        assert 'id="account-new-opportunity-form"' in html
        assert 'id="account-contact-form"' in html

        js = client.get("/js/accounts.js").text
        assert "createOpportunity" in js
        assert "fetchContacts" in js
        assert "createContact" in js
        assert "updateContact" in js
        assert "deleteContact" in js
        assert "deal.html?id=" in js


def test_accounts_html_has_sidebar_with_three_nav_items(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/accounts.html").text

    assert 'class="sidebar"' in html
    assert html.count('class="nav-item') == 4
    assert html.count('class="nav-item active"') == 1
