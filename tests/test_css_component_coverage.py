from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_board_css_styles_buttons_and_form_error(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert "button {" in css or "button{" in css
    assert ".form-error" in css
    assert "var(--stamp-gold)" in css or "var(--ink-line)" in css


def test_board_css_restyles_columns_and_cards(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert ".stage-column" in css
    assert ".opportunity-card" in css
    for literal in ("#f4f5f7", "#ddd", "#fdecea", "#611a15"):
        assert literal not in css
