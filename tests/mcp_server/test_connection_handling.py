import httpx
import pytest

from mcp_server.client import CrmApiClient
from mcp_server.errors import McpUpstreamError, McpUpstreamUnreachableError


def test_connect_error_raises_clear_unreachable_message():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused", request=request)

    client = CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )

    with pytest.raises(McpUpstreamUnreachableError) as exc_info:
        client.request("GET", "/accounts")
    assert "crm-api.test" in str(exc_info.value)


def test_upstream_error_status_carries_verbatim_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404, json={"error": "ACCOUNT_NOT_FOUND", "message": "No account with id 99"}
        )

    client = CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )

    with pytest.raises(McpUpstreamError) as exc_info:
        client.request("GET", "/accounts/99")
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "ACCOUNT_NOT_FOUND"
    assert exc_info.value.message == "No account with id 99"
