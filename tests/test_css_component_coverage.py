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

    page_rule_start = css.index("#deal-detail,")
    page_rule_end = css.index("}", page_rule_start)
    page_rule = css[page_rule_start:page_rule_end]
    assert "#contacts-page" in page_rule, (
        "#contacts-page must share the page-container rule with "
        "#deal-detail/#accounts-page, not duplicate the rule body"
    )

    rule_start = css.index("#contacts-list li,")
    rule_end = css.index("}", rule_start)
    rule = css[rule_start:rule_end]
    assert "#all-contacts-list li" in rule, (
        "#all-contacts-list li must share the same list-row treatment as "
        "#contacts-list li / #accounts-list li, not render as a bare bullet list"
    )


def test_board_css_covers_leads_page_elements(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert "#leads-page" in css
    assert "#lead-form" in css

    page_rule_start = css.index("#deal-detail,")
    page_rule_end = css.index("}", page_rule_start)
    page_rule = css[page_rule_start:page_rule_end]
    assert "#leads-page" in page_rule, (
        "#leads-page must share the page-container rule with "
        "#deal-detail/#accounts-page/#contacts-page, not duplicate the rule body"
    )

    rule_start = css.index("#contacts-list li,")
    rule_end = css.index("}", rule_start)
    rule = css[rule_start:rule_end]
    assert "#leads-list li" in rule, (
        "#leads-list li must share the same list-row treatment as the other list views, "
        "not render as a bare bullet list"
    )


def test_board_css_covers_help_button_and_panel(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert ".help-btn" in css
    assert ".help-panel" in css

    utilities_start = css.index(".header-utilities {")
    utilities_end = css.index("}", utilities_start)
    assert "position: relative" in css[utilities_start:utilities_end], (
        ".header-utilities must be a positioning context for .help-panel to anchor under it"
    )


def test_board_css_covers_help_center_page(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert "#help-center-page" in css
    assert ".help-center-link" in css
    assert "#faq-search" in css
    assert ".faq-category" in css

    page_rule_start = css.index("#deal-detail,")
    page_rule_end = css.index("}", page_rule_start)
    page_rule = css[page_rule_start:page_rule_end]
    assert "#help-center-page" in page_rule, (
        "#help-center-page must share the page-container rule with the other pages, "
        "not duplicate the rule body"
    )
