from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from mock_salesforce.db import get_connection
from mock_salesforce.models import AccountCreate, AccountOut

router = APIRouter()


@router.post("/accounts", response_model=AccountOut, status_code=201)
def create_account(payload: AccountCreate) -> AccountOut:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
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
        return AccountOut(**dict(row))
    finally:
        conn.close()


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts() -> list[AccountOut]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM accounts ORDER BY created_at, id").fetchall()
        return [AccountOut(**dict(r)) for r in rows]
    finally:
        conn.close()


@router.get("/accounts/{account_id}", response_model=AccountOut)
def get_account(account_id: int) -> AccountOut:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "ACCOUNT_NOT_FOUND", "message": f"No account with id {account_id}"},
            )
        return AccountOut(**dict(row))
    finally:
        conn.close()
