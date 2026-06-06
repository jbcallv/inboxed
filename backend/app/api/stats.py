from fastapi import APIRouter, Depends, HTTPException
from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/campaigns", tags=["stats"])


@router.get("/{campaign_id}/stats")
def campaign_stats(campaign_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    _assert_owns(campaign_id, user, db)

    contacts = db.table("contacts").select("status").eq("campaign_id", campaign_id).execute()
    status_counts: dict[str, int] = {}
    for row in contacts.data:
        s = row["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    contact_ids = [r["id"] for r in db.table("contacts").select("id").eq("campaign_id", campaign_id).execute().data]

    replies = 0
    hot_leads = 0
    if contact_ids:
        resp = db.table("responses").select("is_hot_lead").in_("contact_id", contact_ids).execute()
        replies = len(resp.data)
        hot_leads = sum(1 for r in resp.data if r["is_hot_lead"])

    return {
        "status_counts": status_counts,
        "total": len(contacts.data),
        "replies": replies,
        "hot_leads": hot_leads,
    }


def _assert_owns(campaign_id: str, user: dict, db) -> None:
    result = (
        db.table("campaigns")
        .select("id")
        .eq("id", campaign_id)
        .eq("user_id", user["sub"])
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Campaign not found")
