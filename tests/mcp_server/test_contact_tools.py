import httpx
import pytest

from mcp_server.client import CrmApiClient
from mcp_server.errors import McpUpstreamError
from mcp_server.tools import contacts


def make_client(handler) -> CrmApiClient:
    return CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )


def test_list_contacts_without_filter():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/contacts"
        assert dict(request.url.params) == {}
        return httpx.Response(200, json=[{"id": 1, "last_name": "Doe"}])

    client = make_client(handler)
    result = contacts.list_contacts(client)
    assert result == [{"id": 1, "last_name": "Doe"}]


def test_list_contacts_with_account_id_filter():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/contacts"
        assert request.url.params["account_id"] == "7"
        return httpx.Response(200, json=[{"id": 1, "account_id": 7}])

    client = make_client(handler)
    result = contacts.list_contacts(client, account_id=7)
    assert result == [{"id": 1, "account_id": 7}]


def test_get_contact_calls_get_contacts_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/contacts/9"
        return httpx.Response(200, json={"id": 9, "last_name": "Doe"})

    client = make_client(handler)
    result = contacts.get_contact(client, 9)
    assert result == {"id": 9, "last_name": "Doe"}


def test_create_contact_posts_and_returns_created():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/contacts"
        return httpx.Response(201, json={"id": 1, "account_id": 7, "last_name": "Doe"})

    client = make_client(handler)
    result = contacts.create_contact(client, account_id=7, last_name="Doe")
    assert result == {"id": 1, "account_id": 7, "last_name": "Doe"}


def test_create_contact_passes_through_404_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"error": "CONTACT_ACCOUNT_NOT_FOUND", "message": "No account with id 99"},
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        contacts.create_contact(client, account_id=99, last_name="Doe")
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "CONTACT_ACCOUNT_NOT_FOUND"


def test_update_contact_patches_and_returns_updated():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/contacts/1"
        return httpx.Response(200, json={"id": 1, "last_name": "New Name"})

    client = make_client(handler)
    result = contacts.update_contact(client, 1, last_name="New Name")
    assert result == {"id": 1, "last_name": "New Name"}


def test_delete_contact_confirms_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/contacts/1"
        return httpx.Response(204)

    client = make_client(handler)
    result = contacts.delete_contact(client, 1)
    assert result == {"deleted": True, "id": 1}
