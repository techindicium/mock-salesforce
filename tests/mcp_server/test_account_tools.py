import httpx

from mcp_server.client import CrmApiClient
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
