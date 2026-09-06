from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from mock_salesforce.db import get_connection
from mock_salesforce.models import ContactCreate, ContactOut, ContactUpdate

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


@router.get("/contacts", response_model=list[ContactOut])
def list_contacts(account_id: int | None = None) -> list[ContactOut]:
    conn = get_connection()
    try:
        if account_id is not None:
            rows = conn.execute(
                "SELECT * FROM contacts WHERE account_id = ? ORDER BY created_at, id",
                (account_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM contacts ORDER BY created_at, id").fetchall()
        return [ContactOut(**dict(r)) for r in rows]
    finally:
        conn.close()


@router.get("/contacts/{contact_id}", response_model=ContactOut)
def get_contact(contact_id: int) -> ContactOut:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "CONTACT_NOT_FOUND", "message": f"No contact with id {contact_id}"},
            )
        return ContactOut(**dict(row))
    finally:
        conn.close()


@router.patch("/contacts/{contact_id}", response_model=ContactOut)
def update_contact(contact_id: int, payload: ContactUpdate) -> ContactOut:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "CONTACT_NOT_FOUND", "message": f"No contact with id {contact_id}"},
            )
        updates = payload.model_dump(exclude_unset=True)
        if updates:
            now = datetime.now(timezone.utc).isoformat()
            set_clause = ", ".join(f"{field} = ?" for field in updates)
            conn.execute(
                f"UPDATE contacts SET {set_clause}, updated_at = ? WHERE id = ?",
                (*updates.values(), now, contact_id),
            )
            conn.commit()
        row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
        return ContactOut(**dict(row))
    finally:
        conn.close()
