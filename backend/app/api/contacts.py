from fastapi import APIRouter, Depends, HTTPException
from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/{contact_id}")
def get_contact(contact_id: int, user: dict = Depends(get_current_user)):
    db = get_db()
    result = db.table("contacts").select("*").eq("id", contact_id).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "Contact not found")
    contact = result.data[0]
    # verify the owning campaign belongs to this user
    campaign = (
        db.table("campaigns")
        .select("id")
        .eq("id", contact["campaign_id"])
        .eq("user_id", user["sub"])
        .limit(1)
        .execute()
    )
    if not campaign.data:
        raise HTTPException(404, "Contact not found")
    return contact
