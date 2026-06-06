import imaplib
import email
import logging
from datetime import datetime, timezone
from email.header import decode_header
import anthropic
from ..config import settings
from ..db import get_db
from .models import RawReply
from . import suppress as suppress_module

log = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None

_CLASSIFY_PROMPT = """\
Classify this cold email reply into exactly one of:
positive, neutral, negative, unsubscribe

Reply only with the single word. No explanation.\
"""


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def fetch_new_replies() -> list[RawReply]:
    """Connects to Zoho IMAP, fetches unseen messages, marks them seen."""
    try:
        conn = imaplib.IMAP4_SSL(settings.zoho_imap_host)
        conn.login(settings.zoho_imap_user, settings.zoho_imap_password)
        conn.select("INBOX")
        _, uid_data = conn.uid("search", None, "UNSEEN")
        uids = uid_data[0].split() if uid_data[0] else []
        replies = [_fetch_message(conn, uid) for uid in uids]
        conn.logout()
        return [r for r in replies if r is not None]
    except Exception as exc:
        log.error("IMAP error: %s", exc)
        return []


def classify(reply_body: str) -> str:
    """Uses Claude Haiku to classify reply sentiment."""
    client = _get_client()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[
            {
                "role": "user",
                "content": f"{_CLASSIFY_PROMPT}\n\nReply:\n{reply_body[:1000]}",
            }
        ],
    )
    result = message.content[0].text.strip().lower()
    return result if result in {"positive", "neutral", "negative", "unsubscribe"} else "neutral"


def record_reply(reply: RawReply) -> None:
    """Matches reply to a contact, stores it, and updates contact status."""
    db = get_db()
    contact = _find_contact_by_email(db, reply.from_email)
    if contact is None:
        return

    sentiment = classify(reply.body)
    is_hot = sentiment == "positive"

    db.table("responses").insert(
        {
            "contact_id": contact["id"],
            "imap_uid": reply.imap_uid,
            "reply_body": reply.body,
            "sentiment": sentiment,
            "is_hot_lead": is_hot,
            "received_at": reply.received_at.isoformat(),
        }
    ).execute()

    new_status = "hot_lead" if is_hot else (
        "unsubscribed" if sentiment == "unsubscribe" else "replied"
    )
    db.table("contacts").update({"status": new_status}).eq("id", contact["id"]).execute()

    if sentiment == "unsubscribe":
        suppress_module.suppress(reply.from_email, "unsubscribe")


def fetch_and_record_replies() -> None:
    for reply in fetch_new_replies():
        record_reply(reply)


def _fetch_message(conn: imaplib.IMAP4_SSL, uid: bytes) -> RawReply | None:
    try:
        _, msg_data = conn.uid("fetch", uid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        from_email = _parse_address(msg.get("From", ""))
        received_at = _parse_date(msg.get("Date", ""))
        body = _extract_body(msg)
        conn.uid("store", uid, "+FLAGS", "\\Seen")
        return RawReply(
            imap_uid=uid.decode(),
            from_email=from_email,
            body=body,
            received_at=received_at,
        )
    except Exception as exc:
        log.error("Failed to fetch message %s: %s", uid, exc)
        return None


def _parse_address(header: str) -> str:
    import re
    match = re.search(r"<(.+?)>", header)
    if match:
        return match.group(1).strip().lower()
    return header.strip().lower()


def _parse_date(header: str) -> datetime:
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(header)
    except Exception:
        return datetime.now(timezone.utc)


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode("utf-8", errors="replace")
    return ""


def _find_contact_by_email(db, email_addr: str) -> dict | None:
    result = (
        db.table("contacts")
        .select("id,status")
        .eq("email", email_addr)
        .eq("status", "sent")
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
