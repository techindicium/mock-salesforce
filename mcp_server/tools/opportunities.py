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


def create_opportunity(
    client: CrmApiClient,
    *,
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
    payload = {
        "account_id": account_id,
        "name": name,
        "close_date": close_date,
        "stage_name": stage_name,
        "amount": amount,
        "probability": probability,
        "opportunity_type": opportunity_type,
        "lead_source": lead_source,
        "next_step": next_step,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return client.request("POST", "/opportunities", json=payload)
