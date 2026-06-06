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

    responses = (
        db.table("responses")
        .select("sentiment,is_hot_lead,contact_id")
        .execute()
    )
    # filter to contacts in this campaign
    campaign_contact_ids = {r["id"] for r in db.table("contacts").select("id").eq("campaign_id", campaign_id).execute().data}
    campaign_responses = [r for r in responses.data if r["contact_id"] in campaign_contact_ids]

    return {
        "status_counts": status_counts,
        "total": len(contacts.data),
        "replies": len(campaign_responses),
        "hot_leads": sum(1 for r in campaign_responses if r["is_hot_lead"]),
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
