from mcp_server.client import CrmApiClient


def list_contacts(client: CrmApiClient, account_id: int | None = None) -> list[dict]:
    params = {"account_id": account_id} if account_id is not None else None
    return client.request("GET", "/contacts", params=params)


def get_contact(client: CrmApiClient, id: int) -> dict:
    return client.request("GET", f"/contacts/{id}")
