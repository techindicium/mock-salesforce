from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_leads_html_has_sidebar_and_list_container(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/leads.html")
        assert response.status_code == 200
        html = response.text
        assert 'class="sidebar"' in html
        assert html.count('class="nav-item') == 4
        assert html.count('class="nav-item active"') == 1
        assert 'id="leads-page"' in html
        assert 'id="leads-list"' in html
        assert 'id="new-lead-btn"' in html
        assert 'id="lead-form"' in html
        assert 'id="error-banner"' in html
        assert 'type="module"' in html
        assert 'js/leads.js' in html
        assert 'id="lead-id-input"' in html
        assert 'id="lead-form-error"' in html
        assert 'id="lead-last-name-input"' in html
        assert 'id="lead-company-input"' in html
        assert 'id="cancel-lead-form-btn"' in html

        last_name_start = html.index('id="lead-last-name-input"')
        last_name_tag_end = html.index('>', last_name_start)
        assert 'required' in html[last_name_start:last_name_tag_end]

        company_start = html.index('id="lead-company-input"')
        company_tag_end = html.index('>', company_start)
        assert 'required' in html[company_start:company_tag_end]


def test_leads_js_wires_crud_and_convert(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/js/leads.js")
        assert response.status_code == 200
        js = response.text
        assert "createLead" in js
        assert "updateLead" in js
        assert "deleteLead" in js
        assert "convertLead" in js
        assert "edit-lead-btn" in js
        assert "delete-lead-btn" in js
        assert "convert-lead-btn" in js
        assert "confirm(" in js
        assert "from './list-state.js'" in js
        assert "from './form-errors.js'" in js
        assert "from './error-state.js'" in js


def test_all_pages_link_to_leads_page(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        for page in ("/", "/deal.html", "/accounts.html", "/contacts.html"):
            html = client.get(page).text
            assert 'href="leads.html"' in html
