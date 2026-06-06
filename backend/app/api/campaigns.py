import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ..db import get_db
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
    user: dict = Depends(get_current_user),
):
    _assert_owns(campaign_id, user)
    col_map = json.loads(column_map) if column_map else None
    rows = parse_upload(file.file.read(), file.filename or "upload.csv", col_map)

    db = get_db()
    to_insert = [{**row, "campaign_id": campaign_id, "status": "new"} for row in rows]
    if to_insert:
        db.table("contacts").insert(to_insert).execute()

    return {"imported": len(to_insert)}


@router.post("/{campaign_id}/prep")
def prep_campaign(campaign_id: str, user: dict = Depends(get_current_user)):
    _assert_owns(campaign_id, user)
    db = get_db()
    db.table("campaigns").update({"status": "prepping"}).eq("id", campaign_id).execute()
    return StreamingResponse(
        _prep_stream(campaign_id), media_type="text/event-stream"
    )


@router.get("/{campaign_id}/sample")
def get_sample(campaign_id: str, n: int = 5, user: dict = Depends(get_current_user)):
    _assert_owns(campaign_id, user)
    db = get_db()
    result = (
        db.table("outreach_emails")
        .select("id,subject,body,contact_id")
        .eq("status", "draft")
        .limit(n)
        .execute()
    )
    contacts_result = (
        db.table("contacts")
        .select("id,first_name,last_name,company_name,email")
        .eq("campaign_id", campaign_id)
        .execute()
    )
    contacts_map = {c["id"]: c for c in contacts_result.data}

    samples = []
    for email_row in result.data:
        contact = contacts_map.get(email_row["contact_id"], {})
        samples.append({**email_row, "contact": contact})
    return samples


@router.post("/{campaign_id}/launch")
def launch_campaign(campaign_id: str, user: dict = Depends(get_current_user)):
    _assert_owns(campaign_id, user)
    db = get_db()
    # Move all drafted contacts to queued
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


def _prep_stream(campaign_id: str):
    db = get_db()
    contacts_result = (
        db.table("contacts")
        .select("*")
        .eq("campaign_id", campaign_id)
        .eq("status", "new")
        .execute()
    )
    total = len(contacts_result.data)
    kept = 0
    dropped = 0
    yield _sse({"event": "start", "total": total})

    for i, row in enumerate(contacts_result.data):
        contact = Contact(**row)
        contact, warning = _process_contact(contact, db)
        if contact.status in ("drafted", "queued", "verified", "enriched", "enriching", "generating"):
            kept += 1
        elif contact.status in ("rejected", "no_email"):
            dropped += 1
        payload = {"event": "progress", "done": i + 1, "total": total,
                   "status": contact.status, "kept": kept, "dropped": dropped}
        if warning:
            payload["warning"] = warning
        yield _sse(payload)

    db.table("campaigns").update({"status": "ready"}).eq("id", campaign_id).execute()
    yield _sse({"event": "done", "kept": kept, "dropped": dropped})


def _process_contact(contact: Contact, db) -> tuple[Contact, str]:
    """Returns (updated_contact, warning_message). Warning is empty string if none."""
    warning = ""
    try:
        if not contact.email:
            db.table("contacts").update({"status": "finding"}).eq("id", contact.id).execute()
            contact = contact.model_copy(update={"status": "finding"})
            domain = _domain_from_website(contact.company_website)
            if not domain:
                db.table("contacts").update({"status": "no_email", "reject_reason": "no_domain"}).eq("id", contact.id).execute()
                return contact.model_copy(update={"status": "no_email"}), warning
            email = finder_module.find_email(contact.first_name or "", contact.last_name or "", domain)
            if not email:
                db.table("contacts").update({"status": "no_email", "reject_reason": "not_found"}).eq("id", contact.id).execute()
                return contact.model_copy(update={"status": "no_email"}), warning
            db.table("contacts").update({"email": email}).eq("id", contact.id).execute()
            contact = contact.model_copy(update={"email": email})

        db.table("contacts").update({"status": "verifying"}).eq("id", contact.id).execute()
        try:
            contact = verify_module.verify_contact(contact.model_copy(update={"status": "verifying"}))
        except Exception as exc:
            err = str(exc)
            if "Insufficient credits" in err or "credits" in err.lower():
                warning = "MillionVerifier has no credits — verification skipped. Add credits at app.millionverifier.com"
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
