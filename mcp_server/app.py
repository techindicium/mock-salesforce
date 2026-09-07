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


@mcp.tool()
def create_account(
    name: str,
    account_type: str | None = None,
    industry: str | None = None,
    website: str | None = None,
    phone: str | None = None,
    billing_street: str | None = None,
    billing_city: str | None = None,
    billing_state: str | None = None,
    billing_postal_code: str | None = None,
    billing_country: str | None = None,
) -> dict:
    """Create an Account. `name` is required."""
    return accounts.create_account(
        client,
        name=name,
        account_type=account_type,
        industry=industry,
        website=website,
        phone=phone,
        billing_street=billing_street,
        billing_city=billing_city,
        billing_state=billing_state,
        billing_postal_code=billing_postal_code,
        billing_country=billing_country,
    )


@mcp.tool()
def update_account(
    id: int,
    name: str | None = None,
    account_type: str | None = None,
    industry: str | None = None,
    website: str | None = None,
    phone: str | None = None,
    billing_street: str | None = None,
    billing_city: str | None = None,
    billing_state: str | None = None,
    billing_postal_code: str | None = None,
    billing_country: str | None = None,
) -> dict:
    """Update one or more mutable Account fields."""
    return accounts.update_account(
        client,
        id,
        name=name,
        account_type=account_type,
        industry=industry,
        website=website,
        phone=phone,
        billing_street=billing_street,
        billing_city=billing_city,
        billing_state=billing_state,
        billing_postal_code=billing_postal_code,
        billing_country=billing_country,
    )


@mcp.tool()
def delete_account(id: int) -> dict:
    """Delete an Account. Errors verbatim with 409/ACCOUNT_HAS_DEPENDENTS if it
    still has Contacts or Opportunities."""
    return accounts.delete_account(client, id)


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
