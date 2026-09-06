from datetime import datetime, timezone

from fastapi import APIRouter

from mock_salesforce.db import get_connection
from mock_salesforce.models import AccountCreate, AccountOut

router = APIRouter()


@router.post("/accounts", response_model=AccountOut, status_code=201)
def create_account(payload: AccountCreate) -> AccountOut:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO accounts (
            name, account_type, industry, website, phone,
            billing_street, billing_city, billing_state,
            billing_postal_code, billing_country, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.name, payload.account_type, payload.industry, payload.website,
            payload.phone, payload.billing_street, payload.billing_city,
            payload.billing_state, payload.billing_postal_code, payload.billing_country,
            now, now,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return AccountOut(**dict(row))
