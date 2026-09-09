from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"

PAGES = ["/", "/deal.html", "/accounts.html", "/contacts.html", "/leads.html", "/help.html"]


def test_all_pages_render_the_help_button_and_panel(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        for page in PAGES:
            html = client.get(page).text
            assert 'id="help-btn"' in html, page
            assert 'aria-haspopup="true"' in html, page
            assert 'aria-expanded="false"' in html, page
            assert 'id="help-panel"' in html, page
            assert 'id="help-panel-title"' in html, page
            assert 'id="help-panel-body"' in html, page
            assert 'id="help-nav-overview"' in html, page
            assert 'js/help.js' in html, page
            assert 'class="help-center-link" href="help.html"' in html, page

            panel_start = html.index('id="help-panel"')
            panel_tag_end = html.index('>', panel_start)
            assert 'hidden' in html[panel_start:panel_tag_end], page


def test_help_js_and_help_content_js_are_served(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        help_js = client.get("/js/help.js")
        assert help_js.status_code == 200
        assert "javascript" in help_js.headers["content-type"]
        text = help_js.text
        assert "from './help-content.js'" in text
        assert "getPageHelp" in text
        assert "'Escape'" in text
        assert "aria-expanded" in text

        content_js = client.get("/js/help-content.js")
        assert content_js.status_code == 200
        content_text = content_js.text
        assert "HELP_CONTENT" in content_text
        assert "NAV_OVERVIEW" in content_text
        assert "getPageHelp" in content_text


def test_help_content_covers_every_pages_main_id(tmp_path, monkeypatch):
    # Each page's <main id="..."> must have a matching entry in help-content.js,
    # otherwise every real page would silently hit the generic fallback (BEH-5
    # is meant for a hypothetical future page, not any of these five).
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        content_js = client.get("/js/help-content.js").text
        for main_id in (
            "board", "deal-detail", "accounts-page", "contacts-page", "leads-page",
            "help-center-page",
        ):
            assert f"'{main_id}'" in content_js, main_id
