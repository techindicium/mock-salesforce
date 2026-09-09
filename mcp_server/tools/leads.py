from mcp_server.client import CrmApiClient


def list_leads(
    client: CrmApiClient,
    status: str | None = None,
    converted: bool | None = None,
) -> list[dict]:
    params = {}
    if status is not None:
        params["status"] = status
    if converted is not None:
        params["converted"] = converted
    return client.request("GET", "/leads", params=params or None)


def get_lead(client: CrmApiClient, id: int) -> dict:
    return client.request("GET", f"/leads/{id}")


def create_lead(
    client: CrmApiClient,
    *,
    last_name: str,
    company: str,
    first_name: str | None = None,
    title: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    lead_source: str | None = None,
    status: str | None = None,
    rating: str | None = None,
) -> dict:
    payload = {
        "last_name": last_name,
        "company": company,
        "first_name": first_name,
        "title": title,
        "email": email,
        "phone": phone,
        "lead_source": lead_source,
        "status": status,
        "rating": rating,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return client.request("POST", "/leads", json=payload)


def update_lead(client: CrmApiClient, id: int, **fields) -> dict:
    payload = {k: v for k, v in fields.items() if v is not None}
    return client.request("PATCH", f"/leads/{id}", json=payload)


def delete_lead(client: CrmApiClient, id: int) -> dict:
    client.request("DELETE", f"/leads/{id}")
    return {"deleted": True, "id": id}


def convert_lead(
    client: CrmApiClient,
    id: int,
    *,
    account_id: int | None = None,
    contact_id: int | None = None,
    create_opportunity: bool = False,
    opportunity_name: str | None = None,
    opportunity_close_date: str | None = None,
) -> dict:
    payload = {
        "account_id": account_id,
        "contact_id": contact_id,
        "create_opportunity": create_opportunity,
        "opportunity_name": opportunity_name,
        "opportunity_close_date": opportunity_close_date,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return client.request("POST", f"/leads/{id}/convert", json=payload)
