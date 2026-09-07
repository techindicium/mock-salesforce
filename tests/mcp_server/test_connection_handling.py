import httpx
import pytest

import mcp_server.app as app_module
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


ACCOUNT_AND_CONTACT_TOOL_CALLS = [
    lambda: app_module.list_accounts(),
    lambda: app_module.get_account(id=1),
    lambda: app_module.create_account(name="Acme"),
    lambda: app_module.update_account(id=1, name="Acme"),
    lambda: app_module.delete_account(id=1),
    lambda: app_module.list_contacts(),
    lambda: app_module.get_contact(id=1),
    lambda: app_module.create_contact(account_id=1, last_name="Doe"),
    lambda: app_module.update_contact(id=1, last_name="Doe"),
    lambda: app_module.delete_contact(id=1),
]


def test_every_tool_surfaces_a_clear_connection_error(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused", request=request)

    unreachable_client = CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )
    monkeypatch.setattr(app_module, "client", unreachable_client)

    for call in ACCOUNT_AND_CONTACT_TOOL_CALLS:
        with pytest.raises(McpUpstreamUnreachableError):
            call()


def test_all_ten_account_and_contact_tools_registered():
    tool_names = {t.name for t in app_module.mcp._tool_manager.list_tools()}
    expected = {
        "list_accounts", "get_account", "create_account", "update_account", "delete_account",
        "list_contacts", "get_contact", "create_contact", "update_contact", "delete_contact",
        "list_opportunities", "get_opportunity", "create_opportunity", "update_opportunity",
    }
    assert tool_names == expected
    # NOTE: if `mcp._tool_manager.list_tools()` doesn't match the installed
    # `mcp` SDK version's actual introspection surface, find the correct
    # attribute/method for "list registered tools" on the installed version
    # and adjust this assertion accordingly — do not skip the check.
