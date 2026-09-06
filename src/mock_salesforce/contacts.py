from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from mock_salesforce.db import get_connection
from mock_salesforce.models import ContactCreate, ContactOut

router = APIRouter()


@router.post("/contacts", response_model=ContactOut, status_code=201)
def create_contact(payload: ContactCreate) -> ContactOut:
    conn = get_connection()
    try:
        account = conn.execute(
            "SELECT id FROM accounts WHERE id = ?", (payload.account_id,)
        ).fetchone()
        if account is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "CONTACT_ACCOUNT_NOT_FOUND",
                    "message": f"No account with id {payload.account_id}",
                },
            )
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            INSERT INTO contacts (account_id, first_name, last_name, email, phone, title,
                                   created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (payload.account_id, payload.first_name, payload.last_name, payload.email,
             payload.phone, payload.title, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM contacts WHERE id = ?", (cur.lastrowid,)).fetchone()
        return ContactOut(**dict(row))
    finally:
        conn.close()
