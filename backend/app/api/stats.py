from fastapi import APIRouter, Depends, HTTPException
from ..db import get_db
from .auth import get_current_user
from .campaigns import _ALL_STATUSES

router = APIRouter(prefix="/campaigns", tags=["stats"])


@router.get("/{campaign_id}/stats")
def campaign_stats(campaign_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    _assert_owns(campaign_id, user, db)

    # count="exact" per status bypasses Supabase's 1,000-row default
    status_counts: dict[str, int] = {}
    total = 0
    for s in _ALL_STATUSES:
        result = (
            db.table("contacts")
            .select("id", count="exact")
            .eq("campaign_id", campaign_id)
            .eq("status", s)
            .execute()
        )
        n = result.count or 0
        if n:
            status_counts[s] = n
            total += n

    # count responses via campaign join to avoid fetching all contact IDs
    replies_result = (
        db.table("responses")
        .select("is_hot_lead, contacts!inner(campaign_id)", count="exact")
        .eq("contacts.campaign_id", campaign_id)
        .execute()
    )
    replies = replies_result.count or 0
    hot_leads = sum(1 for r in replies_result.data if r.get("is_hot_lead"))

    campaign = db.table("campaigns").select("status").eq("id", campaign_id).single().execute()

    return {
        "status": campaign.data.get("status"),
        "status_counts": status_counts,
        "total": total,
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
