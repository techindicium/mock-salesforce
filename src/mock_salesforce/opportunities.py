from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from mock_salesforce.db import get_connection
from mock_salesforce.models import OpportunityCreate, OpportunityOut

router = APIRouter()

CLOSED_STAGES = {"Closed Won", "Closed Lost"}


def _derive_closed_won(stage_name: str) -> tuple[bool, bool]:
    return stage_name in CLOSED_STAGES, stage_name == "Closed Won"


def _to_opportunity_out(row) -> OpportunityOut:
    data = dict(row)
    data["is_closed"] = bool(data["is_closed"])
    data["is_won"] = bool(data["is_won"])
    return OpportunityOut(**data)


@router.post("/opportunities", response_model=OpportunityOut, status_code=201)
def create_opportunity(payload: OpportunityCreate) -> OpportunityOut:
    conn = get_connection()
    try:
        account = conn.execute(
            "SELECT id FROM accounts WHERE id = ?", (payload.account_id,)
        ).fetchone()
        if account is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "OPPORTUNITY_ACCOUNT_NOT_FOUND",
                    "message": f"No account with id {payload.account_id}",
                },
            )
        is_closed, is_won = _derive_closed_won(payload.stage_name)
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            INSERT INTO opportunities (
                account_id, name, stage_name, amount, close_date, probability,
                opportunity_type, lead_source, next_step, is_closed, is_won,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.account_id, payload.name, payload.stage_name, payload.amount,
                payload.close_date.isoformat(), payload.probability,
                payload.opportunity_type, payload.lead_source, payload.next_step,
                int(is_closed), int(is_won), now, now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM opportunities WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return _to_opportunity_out(row)
    finally:
        conn.close()


@router.get("/opportunities", response_model=list[OpportunityOut])
def list_opportunities() -> list[OpportunityOut]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM opportunities ORDER BY created_at, id").fetchall()
        return [_to_opportunity_out(row) for row in rows]
    finally:
        conn.close()
