import os

from mcp.server.fastmcp import FastMCP

from mcp_server.client import CrmApiClient
from mcp_server.tools import accounts

mcp = FastMCP("mock-salesforce-crm", port=int(os.environ.get("PORT", "8000")))
client = CrmApiClient()


@mcp.tool()
def list_accounts() -> list[dict]:
    """List every Account."""
    return accounts.list_accounts(client)


@mcp.tool()
def get_account(id: int) -> dict:
    """Fetch one Account by id."""
    return accounts.get_account(client, id)


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
