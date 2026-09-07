from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_index_html_has_ten_stage_columns_and_account_switcher(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        html = response.text
        assert html.count('data-stage-column="') == 10
        # These exact ids/classes are the DOM contract a later task's board.js binds against
        # (getElementById + querySelector with no fallback) — asserting only "a <select>
        # exists somewhere" would let this task pass without the hooks that script needs,
        # causing it to throw on a null element and crash the board at runtime.
        assert 'id="account-switcher"' in html
        assert 'id="error-banner"' in html
        assert 'id="board"' in html
        assert 'class="cards"' in html
        assert 'type="module"' in html


def test_board_css_is_served_with_css_content_type(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/css/board.css")
        assert response.status_code == 200
        assert "css" in response.headers["content-type"]


def test_board_js_is_served_and_wires_the_pure_modules(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/js/board.js")
        assert response.status_code == 200
        js = response.text
        assert "from './stages.js'" in js
        assert "from './api.js'" in js
        assert "from './errors.js'" in js
        assert "from './board-state.js'" in js
        assert "dragstart" in js
        assert "'drop'" in js or '"drop"' in js
        assert "account-switcher" in js
        assert "resolveAccountName" in js


def test_board_js_wires_the_per_source_error_state_module(tmp_path, monkeypatch):
    # Regression check (BEH-5): if one action fails (e.g. GET /accounts), the error
    # banner must stay visible even after a later, unrelated action succeeds (e.g.
    # GET /opportunities, or a stage-move PATCH) — that success doesn't mean the
    # original failure is resolved. This is verified behaviorally (not just by
    # string-matching board.js) in static/js/error-state.test.mjs, which exercises
    # the actual per-source reducer via `node --test`; this pytest-side check only
    # confirms board.js is wired to that module rather than reintroducing its own
    # single-scalar error tracking.
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/js/board.js")
        assert response.status_code == 200
        js = response.text
        assert "from './error-state.js'" in js
        assert "reportError" in js
        assert "reportSuccess" in js

    with TestClient(app) as client:
        response = client.get("/js/error-state.js")
        assert response.status_code == 200
        assert "setError" in response.text
        assert "clearError" in response.text
        assert "bannerMessage" in response.text


def test_board_js_wires_create_opportunity_and_card_navigation(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/").text
        assert 'id="new-opportunity-btn"' in html
        assert 'id="create-opportunity-form"' in html

        js = client.get("/js/board.js").text
        assert "createOpportunity" in js
        assert "deal.html?id=" in js
        assert "from './form-errors.js'" in js


def test_board_page_links_to_accounts_page(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/").text
        assert 'href="accounts.html"' in html


def test_index_html_has_sidebar_with_three_nav_items(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/").text

    assert 'class="sidebar"' in html
    assert html.count('class="nav-item') == 3
    assert 'class="nav-item active"' in html
