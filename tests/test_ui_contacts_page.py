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
        assert html.count('class="nav-item') == 3
        assert html.count('class="nav-item active"') == 1
        assert 'id="contacts-page"' in html
        assert 'id="all-contacts-list"' in html
        assert 'type="module"' in html
        select_start = html.index('id="contact-account-select"')
        select_tag_end = html.index('>', select_start)
        assert 'required' in html[select_start:select_tag_end]
