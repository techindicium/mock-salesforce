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
