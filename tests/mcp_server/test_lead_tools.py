import httpx
import pytest

from mcp_server.client import CrmApiClient
from mcp_server.errors import McpUpstreamError
from mcp_server.tools import leads


def make_client(handler) -> CrmApiClient:
    return CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )


def test_list_leads_calls_get_leads_and_returns_unmodified():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json=[{"id": 1, "last_name": "Doe"}])

    client = make_client(handler)
    result = leads.list_leads(client)

    assert seen == {"method": "GET", "path": "/leads"}
    assert result == [{"id": 1, "last_name": "Doe"}]


def test_list_leads_forwards_status_and_converted_filters():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["status"] == "Qualified"
        assert request.url.params["converted"] == "false"
        return httpx.Response(200, json=[])

    client = make_client(handler)
    leads.list_leads(client, status="Qualified", converted=False)


def test_get_lead_calls_get_leads_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/leads/42"
        return httpx.Response(200, json={"id": 42, "last_name": "Doe"})

    client = make_client(handler)
    result = leads.get_lead(client, 42)
    assert result == {"id": 42, "last_name": "Doe"}


def test_create_lead_posts_and_returns_created():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/leads"
        return httpx.Response(201, json={"id": 1, "last_name": "Doe", "company": "Acme"})

    client = make_client(handler)
    result = leads.create_lead(client, last_name="Doe", company="Acme")
    assert result == {"id": 1, "last_name": "Doe", "company": "Acme"}


def test_update_lead_patches_and_returns_updated():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/leads/1"
        return httpx.Response(200, json={"id": 1, "status": "Contacted"})

    client = make_client(handler)
    result = leads.update_lead(client, 1, status="Contacted")
    assert result == {"id": 1, "status": "Contacted"}


def test_delete_lead_confirms_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/leads/1"
        return httpx.Response(204)

    client = make_client(handler)
    result = leads.delete_lead(client, 1)
    assert result == {"deleted": True, "id": 1}


def test_delete_lead_passes_through_409_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={"error": "LEAD_ALREADY_CONVERTED", "message": "Lead 1 is already converted"},
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        leads.delete_lead(client, 1)
    assert exc_info.value.status_code == 409
    assert exc_info.value.error_code == "LEAD_ALREADY_CONVERTED"


def test_convert_lead_posts_only_given_fields():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = request.content
        return httpx.Response(200, json={"id": 1, "converted": True})

    client = make_client(handler)
    result = leads.convert_lead(client, 1, account_id=7)
    assert seen["path"] == "/leads/1/convert"
    assert b'"account_id":7' in seen["body"] or b'"account_id": 7' in seen["body"]
    assert b"contact_id" not in seen["body"]
    assert result == {"id": 1, "converted": True}


def test_convert_lead_passes_through_404_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"error": "LEAD_NOT_FOUND", "message": "No lead with id 999"},
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        leads.convert_lead(client, 999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "LEAD_NOT_FOUND"
