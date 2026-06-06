import base64
import hashlib
import hmac
import logging
from fastapi import APIRouter, HTTPException, Request, Header
from ..config import settings
from ..db import get_db
from ..core import suppress as suppress_module
from ..core.domains import record_bounce, record_complaint

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
log = logging.getLogger(__name__)


@router.post("/resend")
async def resend_webhook(
    request: Request,
    svix_id: str = Header(alias="svix-id"),
    svix_timestamp: str = Header(alias="svix-timestamp"),
    svix_signature: str = Header(alias="svix-signature"),
):
    payload = await request.body()
    if not _verify_signature(payload, svix_id, svix_timestamp, svix_signature):
        raise HTTPException(400, "Invalid webhook signature")

    data = await request.json()
    event_type = data.get("type", "")

    if event_type == "email.bounced":
        _handle_bounce(data)
    elif event_type == "email.complained":
        _handle_complaint(data)
    elif event_type == "email.delivered":
        _handle_delivered(data)

    return {"ok": True}


def _handle_bounce(data: dict) -> None:
    email_addr = _extract_email(data)
    message_id = _extract_message_id(data)
    if email_addr:
        suppress_module.suppress(email_addr, "bounce")
    if message_id:
        db = get_db()
        db.table("outreach_emails").update({"status": "bounced"}).eq(
            "resend_message_id", message_id
        ).execute()
        domain_id = _find_domain_id(db, message_id)
        if domain_id:
            record_bounce(domain_id)


def _handle_complaint(data: dict) -> None:
    email_addr = _extract_email(data)
    message_id = _extract_message_id(data)
    if email_addr:
        suppress_module.suppress(email_addr, "complaint")
    if message_id:
        db = get_db()
        domain_id = _find_domain_id(db, message_id)
        if domain_id:
            record_complaint(domain_id)


def _handle_delivered(data: dict) -> None:
    pass  # delivery confirmation; stats are already recorded at send time


def _verify_signature(payload: bytes, svix_id: str, svix_timestamp: str, svix_signature: str) -> bool:
    secret = settings.resend_webhook_secret
    secret_bytes = base64.b64decode(secret.removeprefix("whsec_"))
    msg = f"{svix_id}.{svix_timestamp}.{payload.decode()}".encode()
    expected = base64.b64encode(
        hmac.new(secret_bytes, msg, hashlib.sha256).digest()
    ).decode()
    return any(
        sig.split(",", 1)[1] == expected
        for sig in svix_signature.split(" ")
        if "," in sig
    )


def _extract_email(data: dict) -> str | None:
    return data.get("data", {}).get("to", [None])[0]


def _extract_message_id(data: dict) -> str | None:
    return data.get("data", {}).get("email_id")


def _find_domain_id(db, message_id: str) -> str | None:
    email_result = (
        db.table("outreach_emails")
        .select("contact_id")
        .eq("resend_message_id", message_id)
        .limit(1)
        .execute()
    )
    if not email_result.data:
        return None
    contact_id = email_result.data[0]["contact_id"]
    contact_result = (
        db.table("contacts")
        .select("domain_id")
        .eq("id", contact_id)
        .limit(1)
        .execute()
    )
    return contact_result.data[0]["domain_id"] if contact_result.data else None
