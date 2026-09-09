from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_help_center_html_has_search_and_faq_container(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/help.html")
        assert response.status_code == 200
        html = response.text
        assert 'class="sidebar"' in html
        # Help Center is not one of the four business-object nav items, so none is active.
        assert html.count('class="nav-item') == 4
        assert html.count('class="nav-item active"') == 0
        assert 'id="help-center-page"' in html
        assert 'id="faq-search"' in html
        assert 'id="faq-list"' in html
        assert 'id="faq-empty-state"' in html
        assert 'js/help-center.js' in html
        assert 'js/help.js' in html

        empty_state_start = html.index('id="faq-empty-state"')
        empty_state_tag_end = html.index('>', empty_state_start)
        assert 'hidden' in html[empty_state_start:empty_state_tag_end]


def test_help_center_js_and_faq_content_js_are_served(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        help_center_js = client.get("/js/help-center.js")
        assert help_center_js.status_code == 200
        text = help_center_js.text
        assert "from './faq-content.js'" in text
        assert "filterFaqs" in text
        assert "'input'" in text
        assert "details" in text.lower()

        faq_content_js = client.get("/js/faq-content.js")
        assert faq_content_js.status_code == 200
        content_text = faq_content_js.text
        assert "FAQ_CATEGORIES" in content_text
        assert "filterFaqs" in content_text
        for category in ("General", "Opportunities", "Accounts", "Contacts", "Leads"):
            assert category in content_text


def test_all_pages_link_to_help_center(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        for page in ("/", "/deal.html", "/accounts.html", "/contacts.html", "/leads.html"):
            html = client.get(page).text
            assert 'href="help.html"' in html, page
