from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from mock_salesforce.db import get_connection
from mock_salesforce.models import LeadConvert, LeadCreate, LeadOut, LeadUpdate

router = APIRouter()


def _to_lead_out(row) -> LeadOut:
    data = dict(row)
    data["converted"] = data["converted_at"] is not None
    return LeadOut(**data)


def _get_lead_row(conn, lead_id: int):
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "LEAD_NOT_FOUND", "message": f"No lead with id {lead_id}"},
        )
    return row


def _require_unconverted(row) -> None:
    if row["converted_at"] is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "LEAD_ALREADY_CONVERTED",
                "message": f"Lead {row['id']} is already converted",
            },
        )


@router.post("/leads", response_model=LeadOut, status_code=201)
def create_lead(payload: LeadCreate) -> LeadOut:
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            INSERT INTO leads (
                first_name, last_name, company, title, email, phone,
                lead_source, status, rating, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.first_name, payload.last_name, payload.company, payload.title,
                payload.email, payload.phone, payload.lead_source, payload.status,
                payload.rating, now, now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _to_lead_out(row)
    finally:
        conn.close()


@router.get("/leads", response_model=list[LeadOut])
def list_leads(status: str | None = None, converted: bool | None = None) -> list[LeadOut]:
    conn = get_connection()
    try:
        query = "SELECT * FROM leads WHERE 1=1"
        params: list = []
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        if converted is not None:
            query += " AND converted_at IS NOT NULL" if converted else " AND converted_at IS NULL"
        query += " ORDER BY created_at, id"
        rows = conn.execute(query, params).fetchall()
        return [_to_lead_out(r) for r in rows]
    finally:
        conn.close()


@router.get("/leads/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int) -> LeadOut:
    conn = get_connection()
    try:
        return _to_lead_out(_get_lead_row(conn, lead_id))
    finally:
        conn.close()


@router.patch("/leads/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: int, payload: LeadUpdate) -> LeadOut:
    conn = get_connection()
    try:
        row = _get_lead_row(conn, lead_id)
        _require_unconverted(row)
        updates = payload.model_dump(exclude_unset=True)
        if updates:
            now = datetime.now(timezone.utc).isoformat()
            set_clause = ", ".join(f"{field} = ?" for field in updates)
            conn.execute(
                f"UPDATE leads SET {set_clause}, updated_at = ? WHERE id = ?",
                (*updates.values(), now, lead_id),
            )
            conn.commit()
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return _to_lead_out(row)
    finally:
        conn.close()


@router.delete("/leads/{lead_id}", status_code=204)
def delete_lead(lead_id: int) -> None:
    conn = get_connection()
    try:
        row = _get_lead_row(conn, lead_id)
        _require_unconverted(row)
        conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        conn.commit()
    finally:
        conn.close()


@router.post("/leads/{lead_id}/convert", response_model=LeadOut)
def convert_lead(lead_id: int, payload: LeadConvert = LeadConvert()) -> LeadOut:
    conn = get_connection()
    try:
        row = _get_lead_row(conn, lead_id)
        _require_unconverted(row)
        now = datetime.now(timezone.utc).isoformat()

        if payload.account_id is not None:
            account = conn.execute(
                "SELECT id FROM accounts WHERE id = ?", (payload.account_id,)
            ).fetchone()
            if account is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "LEAD_CONVERT_ACCOUNT_NOT_FOUND",
                        "message": f"No account with id {payload.account_id}",
                    },
                )
            account_id = payload.account_id
        else:
            cur = conn.execute(
                """
                INSERT INTO accounts (name, created_at, updated_at) VALUES (?, ?, ?)
                """,
                (row["company"], now, now),
            )
            account_id = cur.lastrowid

        if payload.contact_id is not None:
            contact = conn.execute(
                "SELECT id, account_id FROM contacts WHERE id = ?", (payload.contact_id,)
            ).fetchone()
            if contact is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "LEAD_CONVERT_CONTACT_NOT_FOUND",
                        "message": f"No contact with id {payload.contact_id}",
                    },
                )
            if contact["account_id"] != account_id:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "LEAD_CONVERT_CONTACT_ACCOUNT_MISMATCH",
                        "message": (
                            f"Contact {payload.contact_id} does not belong to "
                            f"account {account_id}"
                        ),
                    },
                )
            contact_id = payload.contact_id
        else:
            cur = conn.execute(
                """
                INSERT INTO contacts (
                    account_id, first_name, last_name, email, phone, title,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_id, row["first_name"], row["last_name"], row["email"],
                    row["phone"], row["title"], now, now,
                ),
            )
            contact_id = cur.lastrowid

        opportunity_id = None
        if payload.create_opportunity:
            if payload.opportunity_close_date is None:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "VALIDATION_ERROR",
                        "message": (
                            "opportunity_close_date: required when create_opportunity is true"
                        ),
                    },
                )
            opportunity_name = payload.opportunity_name or row["company"]
            cur = conn.execute(
                """
                INSERT INTO opportunities (
                    account_id, name, stage_name, amount, close_date, probability,
                    opportunity_type, lead_source, next_step, is_closed, is_won,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_id, opportunity_name, "Prospecting", None,
                    payload.opportunity_close_date.isoformat(), None, None,
                    row["lead_source"], None, 0, 0, now, now,
                ),
            )
            opportunity_id = cur.lastrowid

        conn.execute(
            """
            UPDATE leads SET
                converted_at = ?, converted_account_id = ?, converted_contact_id = ?,
                converted_opportunity_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (now, account_id, contact_id, opportunity_id, now, lead_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return _to_lead_out(row)
    finally:
        conn.close()
