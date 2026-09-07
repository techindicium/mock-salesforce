import os

from mcp.server.fastmcp import FastMCP

from mcp_server.client import CrmApiClient
from mcp_server.tools import accounts, contacts, opportunities

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


@mcp.tool()
def list_contacts(account_id: int | None = None) -> list[dict]:
    """List Contacts, optionally filtered by `account_id`."""
    return contacts.list_contacts(client, account_id)


@mcp.tool()
def get_contact(id: int) -> dict:
    """Fetch one Contact by id."""
    return contacts.get_contact(client, id)


@mcp.tool()
def create_contact(
    account_id: int,
    last_name: str,
    first_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    title: str | None = None,
) -> dict:
    """Create a Contact under an Account. `account_id` and `last_name` are required."""
    return contacts.create_contact(
        client,
        account_id=account_id,
        last_name=last_name,
        first_name=first_name,
        email=email,
        phone=phone,
        title=title,
    )


@mcp.tool()
def update_contact(
    id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    title: str | None = None,
) -> dict:
    """Update one or more mutable Contact fields."""
    return contacts.update_contact(
        client,
        id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        title=title,
    )


@mcp.tool()
def delete_contact(id: int) -> dict:
    """Delete a Contact."""
    return contacts.delete_contact(client, id)


@mcp.tool()
def list_opportunities(
    account_id: int | None = None, stage_name: str | None = None
) -> list[dict]:
    """List Opportunities, optionally filtered by `account_id` and/or `stage_name`."""
    return opportunities.list_opportunities(client, account_id, stage_name)


@mcp.tool()
def get_opportunity(id: int) -> dict:
    """Fetch one Opportunity by id."""
    return opportunities.get_opportunity(client, id)


@mcp.tool()
def create_opportunity(
    account_id: int,
    name: str,
    close_date: str,
    stage_name: str | None = None,
    amount: float | None = None,
    probability: float | None = None,
    opportunity_type: str | None = None,
    lead_source: str | None = None,
    next_step: str | None = None,
) -> dict:
    """Create an Opportunity under an Account. `account_id`, `name`, and
    `close_date` are required; `stage_name` defaults to Prospecting."""
    return opportunities.create_opportunity(
        client,
        account_id=account_id,
        name=name,
        close_date=close_date,
        stage_name=stage_name,
        amount=amount,
        probability=probability,
        opportunity_type=opportunity_type,
        lead_source=lead_source,
        next_step=next_step,
    )


@mcp.tool()
def update_opportunity(
    id: int,
    name: str | None = None,
    stage_name: str | None = None,
    amount: float | None = None,
    close_date: str | None = None,
    probability: float | None = None,
    opportunity_type: str | None = None,
    lead_source: str | None = None,
    next_step: str | None = None,
) -> dict:
    """Update one or more mutable Opportunity fields, including `stage_name` transitions."""
    return opportunities.update_opportunity(
        client,
        id,
        name=name,
        stage_name=stage_name,
        amount=amount,
        close_date=close_date,
        probability=probability,
        opportunity_type=opportunity_type,
        lead_source=lead_source,
        next_step=next_step,
    )


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
