from mcp_server.client import CrmApiClient


def list_opportunities(
    client: CrmApiClient,
    account_id: int | None = None,
    stage_name: str | None = None,
) -> list[dict]:
    params = {}
    if account_id is not None:
        params["account_id"] = account_id
    if stage_name is not None:
        params["stage_name"] = stage_name
    return client.request("GET", "/opportunities", params=params or None)


def get_opportunity(client: CrmApiClient, id: int) -> dict:
    return client.request("GET", f"/opportunities/{id}")
