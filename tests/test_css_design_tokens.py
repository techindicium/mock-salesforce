from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_board_css_defines_design_tokens(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert ":root" in css
    for token in ("--brand", "--brand-dark", "--surface", "--surface-alt", "--border", "--error", "--success"):
        assert token in css


def test_board_css_hidden_guard_is_important(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert "[hidden]" in css
    hidden_rule_start = css.index("[hidden]")
    hidden_rule = css[hidden_rule_start:hidden_rule_start + 80]
    assert "!important" in hidden_rule
