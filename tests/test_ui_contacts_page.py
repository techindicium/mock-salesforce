from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_contacts_html_has_sidebar_and_list_container(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/contacts.html")
        assert response.status_code == 200
        html = response.text
        assert html.count('class="nav-item') == 4
        assert html.count('class="nav-item active"') == 1
        assert 'id="contacts-page"' in html
        assert 'id="all-contacts-list"' in html
        assert 'type="module"' in html
        select_start = html.index('id="contact-account-select"')
        select_tag_end = html.index('>', select_start)
        assert 'required' in html[select_start:select_tag_end]


def test_contacts_html_has_edit_and_delete_buttons_per_row(tmp_path, monkeypatch):
    # This is a structural smoke test only — the per-row edit/delete buttons are
    # rendered by contacts.js at runtime (dataset-driven, like accounts.js's
    # edit-account-btn/delete-account-btn), so this test asserts the JS file
    # references the expected class hooks rather than asserting on static HTML.
    contacts_js = (STATIC_DIR / "js" / "contacts.js").read_text()
    assert "edit-contact-btn" in contacts_js
    assert "delete-contact-btn" in contacts_js
    assert "createContact" in contacts_js
    assert "updateContact" in contacts_js
    assert "deleteContact" in contacts_js
    assert "confirm(" in contacts_js
