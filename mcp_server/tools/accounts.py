from mcp_server.client import CrmApiClient


def list_accounts(client: CrmApiClient) -> list[dict]:
    return client.request("GET", "/accounts")


def get_account(client: CrmApiClient, id: int) -> dict:
    return client.request("GET", f"/accounts/{id}")
