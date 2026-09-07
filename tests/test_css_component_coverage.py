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


def test_list_row_rule_sets_explicit_text_color(tmp_path, monkeypatch):
    """#contacts-list li / #accounts-list li set a paper-dim background but must
    also set their own text color rather than relying on ancestor inheritance —
    on deal.html the row inherits dark text from its #contacts-section ancestor
    (which does set color), but #accounts-list li has no such ancestor, so
    without an explicit color it inherits body's light --paper-text-on-rail
    (meant for text on the dark page background) onto a light paper-dim row,
    producing near-invisible low-contrast text."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    rule_start = css.index("#contacts-list li,")
    rule_end = css.index("}", rule_start)
    rule = css[rule_start:rule_end]
    assert "color:" in rule, (
        "#contacts-list li / #accounts-list li must declare an explicit text "
        "color — do not rely on ancestor inheritance for contrast"
    )


def test_board_css_defines_sidebar_shell(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    for selector in (".app-shell", ".sidebar", ".nav-item", ".nav-item:hover", ".nav-item.active", ".app-main"):
        assert selector in css


def test_board_css_covers_contacts_page_elements(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert "#contacts-page" in css
    assert "#all-contacts-list" in css

    rule_start = css.index("#contacts-list li,")
    rule_end = css.index("}", rule_start)
    rule = css[rule_start:rule_end]
    assert "#all-contacts-list li" in rule, (
        "#all-contacts-list li must share the same list-row treatment as "
        "#contacts-list li / #accounts-list li, not render as a bare bullet list"
    )
