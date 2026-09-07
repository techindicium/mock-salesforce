from mcp_server.client import CrmApiClient


def list_contacts(client: CrmApiClient, account_id: int | None = None) -> list[dict]:
    params = {"account_id": account_id} if account_id is not None else None
    return client.request("GET", "/contacts", params=params)


def get_contact(client: CrmApiClient, id: int) -> dict:
    return client.request("GET", f"/contacts/{id}")


def create_contact(
    client: CrmApiClient,
    *,
    account_id: int,
    last_name: str,
    first_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    title: str | None = None,
) -> dict:
    payload = {
        "account_id": account_id,
        "last_name": last_name,
        "first_name": first_name,
        "email": email,
        "phone": phone,
        "title": title,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return client.request("POST", "/contacts", json=payload)


def update_contact(client: CrmApiClient, id: int, **fields) -> dict:
    payload = {k: v for k, v in fields.items() if v is not None}
    return client.request("PATCH", f"/contacts/{id}", json=payload)


def delete_contact(client: CrmApiClient, id: int) -> dict:
    client.request("DELETE", f"/contacts/{id}")
    return {"deleted": True, "id": id}
