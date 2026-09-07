import httpx

from mcp_server.client import CrmApiClient
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
