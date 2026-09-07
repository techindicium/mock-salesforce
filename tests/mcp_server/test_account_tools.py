import httpx
import pytest

from mcp_server.client import CrmApiClient
from mcp_server.errors import McpUpstreamError
from mcp_server.tools import accounts


def make_client(handler) -> CrmApiClient:
    return CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )


def test_list_accounts_calls_get_accounts_and_returns_unmodified():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json=[{"id": 1, "name": "Acme"}])

    client = make_client(handler)
    result = accounts.list_accounts(client)

    assert seen == {"method": "GET", "path": "/accounts"}
    assert result == [{"id": 1, "name": "Acme"}]


def test_get_account_calls_get_accounts_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/accounts/42"
        return httpx.Response(200, json={"id": 42, "name": "Acme"})

    client = make_client(handler)
    result = accounts.get_account(client, 42)
    assert result == {"id": 42, "name": "Acme"}


def test_create_account_posts_and_returns_created():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/accounts"
        return httpx.Response(201, json={"id": 1, "name": "Acme"})

    client = make_client(handler)
    result = accounts.create_account(client, name="Acme")
    assert result == {"id": 1, "name": "Acme"}


def test_update_account_patches_and_returns_updated():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/accounts/1"
        return httpx.Response(200, json={"id": 1, "name": "New Name"})

    client = make_client(handler)
    result = accounts.update_account(client, 1, name="New Name")
    assert result == {"id": 1, "name": "New Name"}


def test_delete_account_confirms_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/accounts/1"
        return httpx.Response(204)

    client = make_client(handler)
    result = accounts.delete_account(client, 1)
    assert result == {"deleted": True, "id": 1}


def test_delete_account_passes_through_409_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "error": "ACCOUNT_HAS_DEPENDENTS",
                "message": "Account 1 has 2 dependent record(s)",
            },
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        accounts.delete_account(client, 1)
    assert exc_info.value.status_code == 409
    assert exc_info.value.error_code == "ACCOUNT_HAS_DEPENDENTS"
    assert exc_info.value.message == "Account 1 has 2 dependent record(s)"
