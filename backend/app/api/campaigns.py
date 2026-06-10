import asyncio
import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ..db import get_db
from ..config import settings
from ..core.ingest import parse_upload
from ..core.models import Contact
from ..core import (
    verify as verify_module,
    enrich as enrich_module,
    generate as generate_module,
    finder as finder_module,
)
from .auth import get_current_user

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
log = logging.getLogger(__name__)


class CampaignCreate(BaseModel):
    name: str


@router.get("")
def list_campaigns(user: dict = Depends(get_current_user)):
    db = get_db()
    result = db.table("campaigns").select("*").eq("user_id", user["sub"]).order("created_at", desc=True).execute()
    return result.data


_ALL_STATUSES = ["new", "finding", "verifying", "enriching", "generating", "drafted", "queued", "sent", "rejected", "no_email"]


@router.get("/{campaign_id}")
def get_campaign(campaign_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    _assert_owns(campaign_id, user)
    campaign = db.table("campaigns").select("*").eq("id", campaign_id).single().execute()
    # Use exact count per status to avoid Supabase's 1,000-row default limit
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
    return {**campaign.data, "status_counts": status_counts, "total": total}


@router.post("")
def create_campaign(body: CampaignCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    result = db.table("campaigns").insert(
        {"name": body.name, "user_id": user["sub"]}
    ).execute()
    return result.data[0]


@router.post("/{campaign_id}/upload")
def upload_contacts(
    campaign_id: str,
    file: UploadFile = File(...),
    column_map: str | None = Form(None),
    limit: int | None = Form(None),
    user: dict = Depends(get_current_user),
):
    _assert_owns(campaign_id, user)
    col_map = json.loads(column_map) if column_map else None
    rows = parse_upload(file.file.read(), file.filename or "upload.csv", col_map)
    if limit:
        rows = rows[:limit]

    db = get_db()
    to_insert = [{**row, "campaign_id": campaign_id, "status": "new"} for row in rows]
    if to_insert:
        db.table("contacts").insert(to_insert).execute()

    return {"imported": len(to_insert)}


@router.post("/{campaign_id}/prep")
async def prep_campaign(
    campaign_id: str,
    skip_verification: bool = False,
    limit: int | None = None,
    user: dict = Depends(get_current_user),
):
    _assert_owns(campaign_id, user)
    get_db().table("campaigns").update({"status": "prepping"}).eq("id", campaign_id).execute()
    return StreamingResponse(
        _prep_stream(campaign_id, skip_verification, limit), media_type="text/event-stream"
    )


@router.get("/{campaign_id}/contacts")
def list_contacts(
    campaign_id: str,
    status: str | None = None,
    page: int = 1,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    _assert_owns(campaign_id, user)
    db = get_db()
    q = db.table("contacts").select("*").eq("campaign_id", campaign_id)
    if status:
        q = q.eq("status", status)
    result = q.order("id").range((page - 1) * limit, page * limit - 1).execute()
    return result.data


@router.get("/{campaign_id}/sample")
def get_sample(campaign_id: str, n: int = 5, user: dict = Depends(get_current_user)):
    import random
    _assert_owns(campaign_id, user)
    db = get_db()
    contacts = db.table("contacts").select("id,first_name,last_name,company_name,email").eq("campaign_id", campaign_id).execute().data
    contact_ids = [c["id"] for c in contacts]
    contacts_map = {c["id"]: c for c in contacts}

    if not contact_ids:
        return []

    # Fetch a larger pool then randomly pick n to avoid always showing the first rows
    pool_size = max(n * 5, 50)
    pool = (
        db.table("outreach_emails")
        .select("id,subject,body,contact_id")
        .eq("status", "draft")
        .in_("contact_id", contact_ids)
        .limit(pool_size)
        .execute()
        .data
    )
    emails = random.sample(pool, min(n, len(pool)))
    return [{**e, "contact": contacts_map.get(e["contact_id"], {})} for e in emails]


@router.post("/{campaign_id}/launch")
def launch_campaign(campaign_id: str, user: dict = Depends(get_current_user)):
    _assert_owns(campaign_id, user)
    db = get_db()
    db.table("contacts").update({"status": "queued"}).eq(
        "campaign_id", campaign_id
    ).eq("status", "drafted").execute()
    db.table("campaigns").update({"status": "sending"}).eq("id", campaign_id).execute()
    return {"status": "sending"}


@router.post("/{campaign_id}/pause")
def pause_campaign(campaign_id: str, user: dict = Depends(get_current_user)):
    _assert_owns(campaign_id, user)
    db = get_db()
    db.table("campaigns").update({"status": "paused"}).eq("id", campaign_id).execute()
    return {"status": "paused"}


@router.post("/{campaign_id}/resume")
def resume_campaign(campaign_id: str, user: dict = Depends(get_current_user)):
    _assert_owns(campaign_id, user)
    db = get_db()
    db.table("campaigns").update({"status": "sending"}).eq("id", campaign_id).execute()
    return {"status": "sending"}


async def _prep_stream(campaign_id: str, skip_verification: bool = False, limit: int | None = None):
    q = get_db().table("contacts").select("*").eq("campaign_id", campaign_id).eq("status", "new")
    if limit:
        q = q.limit(limit)
    rows = q.execute().data
    total = len(rows)
    kept = 0
    dropped = 0
    done = 0
    last_warning = ""

    yield _sse({"event": "start", "total": total})

    loop = asyncio.get_event_loop()
    semaphore = asyncio.Semaphore(settings.prep_workers)
    queue: asyncio.Queue = asyncio.Queue()

    async def run_one(row: dict) -> None:
        async with semaphore:
            try:
                result = await loop.run_in_executor(
                    None, _process_contact, Contact(**row), skip_verification
                )
            except Exception as exc:
                log.error("Unhandled prep worker error: %s", exc)
                result = (Contact(**row), "")
            await queue.put(result)

    tasks = [asyncio.create_task(run_one(row)) for row in rows]

    for _ in range(total):
        contact, warning = await queue.get()
        done += 1
        if warning:
            last_warning = warning
        if contact.status in ("drafted", "queued", "verified", "enriched", "enriching", "generating"):
            kept += 1
        elif contact.status in ("rejected", "no_email"):
            dropped += 1
        payload = {"event": "progress", "done": done, "total": total,
                   "status": contact.status, "kept": kept, "dropped": dropped}
        if last_warning:
            payload["warning"] = last_warning
        yield _sse(payload)

    await asyncio.gather(*tasks)
    get_db().table("campaigns").update({"status": "ready"}).eq("id", campaign_id).execute()
    yield _sse({"event": "done", "kept": kept, "dropped": dropped})


def _process_contact(contact: Contact, skip_verification: bool = False) -> tuple[Contact, str]:
    """
    Runs in a worker thread — calls get_db() to get this thread's own client.
    Returns (updated_contact, warning_message).
    """
    db = get_db()
    warning = ""
    try:
        if not contact.email:
            db.table("contacts").update({"status": "finding"}).eq("id", contact.id).execute()
            contact = contact.model_copy(update={"status": "finding"})
            domain = _domain_from_website(contact.company_website)
            email, reason = finder_module.find_email(contact.first_name or "", contact.last_name or "", domain)
            if not email:
                db.table("contacts").update({"status": "no_email", "reject_reason": reason or "not_found"}).eq("id", contact.id).execute()
                return contact.model_copy(update={"status": "no_email"}), warning
            db.table("contacts").update({"email": email}).eq("id", contact.id).execute()
            contact = contact.model_copy(update={"email": email})

        if skip_verification:
            db.table("contacts").update({"status": "verified", "mv_result": "skipped"}).eq("id", contact.id).execute()
            contact = contact.model_copy(update={"status": "verified", "mv_result": "skipped"})
        else:
            db.table("contacts").update({"status": "verifying"}).eq("id", contact.id).execute()
            try:
                contact = verify_module.verify_contact(contact.model_copy(update={"status": "verifying"}))
            except Exception as exc:
                err = str(exc)
                if "Insufficient credits" in err or "credits" in err.lower():
                    warning = "MillionVerifier has no credits — add credits at app.millionverifier.com"
                    db.table("contacts").update({"status": "new"}).eq("id", contact.id).execute()
                    return contact.model_copy(update={"status": "new"}), warning
                raise
            if contact.status != "verified":
                return contact, warning

        db.table("contacts").update({"status": "enriching"}).eq("id", contact.id).execute()
        website_text = ""
        if contact.company_website:
            website_text = enrich_module.scrape_company(contact.company_website)
            db.table("contact_enrichments").upsert(
                {"contact_id": contact.id, "website_content": website_text},
                on_conflict="contact_id",
            ).execute()
        db.table("contacts").update({"status": "enriched"}).eq("id", contact.id).execute()

        db.table("contacts").update({"status": "generating"}).eq("id", contact.id).execute()
        draft = generate_module.generate_email(contact, website_text)
        if draft:
            db.table("outreach_emails").insert(
                {"contact_id": contact.id, "subject": draft.subject, "body": draft.body, "status": "draft"}
            ).execute()
            db.table("contacts").update({"status": "drafted"}).eq("id", contact.id).execute()
            return contact.model_copy(update={"status": "drafted"}), warning

        return contact.model_copy(update={"status": "generating"}), warning
    except Exception as exc:
        log.error("Prep error for contact %s: %s", contact.id, exc)
        return contact, warning


def _domain_from_website(website: str | None) -> str:
    if not website:
        return ""
    import re
    match = re.search(r"https?://(?:www\.)?([^/]+)", website)
    return match.group(1) if match else website


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _assert_owns(campaign_id: str, user: dict) -> None:
    db = get_db()
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
