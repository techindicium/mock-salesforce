from mcp_server.client import CrmApiClient


def list_accounts(client: CrmApiClient) -> list[dict]:
    return client.request("GET", "/accounts")


def get_account(client: CrmApiClient, id: int) -> dict:
    return client.request("GET", f"/accounts/{id}")


def create_account(
    client: CrmApiClient,
    *,
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
    payload = {
        "name": name,
        "account_type": account_type,
        "industry": industry,
        "website": website,
        "phone": phone,
        "billing_street": billing_street,
        "billing_city": billing_city,
        "billing_state": billing_state,
        "billing_postal_code": billing_postal_code,
        "billing_country": billing_country,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return client.request("POST", "/accounts", json=payload)


def update_account(client: CrmApiClient, id: int, **fields) -> dict:
    payload = {k: v for k, v in fields.items() if v is not None}
    return client.request("PATCH", f"/accounts/{id}", json=payload)


def delete_account(client: CrmApiClient, id: int) -> dict:
    client.request("DELETE", f"/accounts/{id}")
    return {"deleted": True, "id": id}
