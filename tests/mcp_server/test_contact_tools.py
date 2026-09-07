import httpx

from mcp_server.client import CrmApiClient
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
