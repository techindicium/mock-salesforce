import httpx
import pytest

from mcp_server.client import CrmApiClient
from mcp_server.errors import McpUpstreamError
from mcp_server.tools import opportunities


def make_client(handler) -> CrmApiClient:
    return CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )


def test_list_opportunities_without_filter():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/opportunities"
        assert dict(request.url.params) == {}
        return httpx.Response(200, json=[{"id": 1, "name": "Deal"}])

    client = make_client(handler)
    result = opportunities.list_opportunities(client)
    assert result == [{"id": 1, "name": "Deal"}]


def test_list_opportunities_with_account_id_and_stage_name_filters():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/opportunities"
        assert request.url.params["account_id"] == "7"
        assert request.url.params["stage_name"] == "Qualification"
        return httpx.Response(200, json=[{"id": 1, "account_id": 7}])

    client = make_client(handler)
    result = opportunities.list_opportunities(
        client, account_id=7, stage_name="Qualification"
    )
    assert result == [{"id": 1, "account_id": 7}]


def test_get_opportunity_calls_get_opportunities_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/opportunities/9"
        return httpx.Response(200, json={"id": 9, "name": "Deal"})

    client = make_client(handler)
    result = opportunities.get_opportunity(client, 9)
    assert result == {"id": 9, "name": "Deal"}


def test_create_opportunity_posts_and_defaults_stage():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/opportunities"
        return httpx.Response(
            201,
            json={
                "id": 1, "account_id": 7, "name": "Big Deal", "stage_name": "Prospecting",
            },
        )

    client = make_client(handler)
    result = opportunities.create_opportunity(
        client, account_id=7, name="Big Deal", close_date="2026-12-01"
    )
    assert result == {
        "id": 1, "account_id": 7, "name": "Big Deal", "stage_name": "Prospecting",
    }


def test_create_opportunity_passes_through_404_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "error": "OPPORTUNITY_ACCOUNT_NOT_FOUND",
                "message": "No account with id 999999",
            },
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        opportunities.create_opportunity(
            client, account_id=999999, name="Big Deal", close_date="2026-12-01"
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "OPPORTUNITY_ACCOUNT_NOT_FOUND"
    assert exc_info.value.message == "No account with id 999999"


def test_create_opportunity_invalid_stage_name_passes_through_422_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422,
            json={
                "error": "VALIDATION_ERROR",
                "message": "stage_name must be one of the ten fixed values",
            },
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        opportunities.create_opportunity(
            client, account_id=1, name="Big Deal", close_date="2026-12-01",
            stage_name="Bogus Stage",
        )
    assert exc_info.value.status_code == 422
    assert exc_info.value.error_code == "VALIDATION_ERROR"


def test_update_opportunity_patches_and_returns_updated():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/opportunities/1"
        return httpx.Response(200, json={"id": 1, "amount": 50000})

    client = make_client(handler)
    result = opportunities.update_opportunity(client, 1, amount=50000)
    assert result == {"id": 1, "amount": 50000}


def test_update_opportunity_stage_name_transition():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/opportunities/1"
        return httpx.Response(200, json={"id": 1, "stage_name": "Closed Won"})

    client = make_client(handler)
    result = opportunities.update_opportunity(client, 1, stage_name="Closed Won")
    assert result == {"id": 1, "stage_name": "Closed Won"}


def test_update_opportunity_invalid_stage_name_passes_through_422_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422,
            json={
                "error": "VALIDATION_ERROR",
                "message": "stage_name must be one of the ten fixed values",
            },
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        opportunities.update_opportunity(client, 1, stage_name="Bogus Stage")
    assert exc_info.value.status_code == 422
    assert exc_info.value.error_code == "VALIDATION_ERROR"


def test_delete_opportunity_confirms_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/opportunities/1"
        return httpx.Response(204)

    client = make_client(handler)
    result = opportunities.delete_opportunity(client, 1)
    assert result == {"deleted": True, "id": 1}
