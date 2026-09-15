from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core import suppress as suppress_module
from ..db import get_db
from ..utils.email_format import normalize

router = APIRouter(prefix="/unsubscribe", tags=["unsubscribe"])


class UnsubscribeRequest(BaseModel):
    email: str
    campaign_id: str


@router.post("")
def unsubscribe(body: UnsubscribeRequest):
    email = normalize(body.email)
    db = get_db()
    contact = (
        db.table("contacts")
        .select("id")
        .eq("campaign_id", body.campaign_id)
        .eq("email", email)
        .limit(1)
        .execute()
    )
    if not contact.data:
        raise HTTPException(404, "No matching contact for this campaign")

    suppress_module.suppress(email, "unsubscribe")
    db.table("contacts").update({"status": "unsubscribed"}).eq(
        "id", contact.data[0]["id"]
    ).execute()
    return {"status": "unsubscribed"}
