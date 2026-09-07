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

    button_start = css.index("button {") if "button {" in css else css.index("button{")
    button_end = css.index("}", button_start)
    button_rule = css[button_start:button_end]
    assert "var(--" in button_rule, "button rule must use a design token, not a hardcoded color"

    form_error_start = css.index(".form-error")
    form_error_end = css.index("}", form_error_start)
    form_error_rule = css[form_error_start:form_error_end]
    assert "var(--" in form_error_rule, (
        ".form-error rule must use a design token, not a hardcoded color"
    )


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


def test_board_css_covers_deal_page_elements(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    for selector in ("#deal-detail", "#contacts-list", "#edit-opportunity-form", "#contact-form"):
        assert selector in css


def test_board_css_covers_accounts_page_elements(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    for selector in ("#accounts-list", ".account-delete-error", "#account-form", "#account-new-opportunity-form", "#account-contact-form"):
        assert selector in css
