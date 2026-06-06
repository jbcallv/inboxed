import random
import resend
from ..config import settings
from ..db import get_db
from .models import Contact, Draft, SendingDomain, SendResult
from . import domains as domain_module


def send_one(domain: SendingDomain, contact: Contact, draft: Draft) -> SendResult:
    """Sends one email via Resend. Rotates from_locals, sets required headers."""
    resend.api_key = settings.resend_api_key
    local = _pick_local(domain)
    from_address = f"{domain.from_name} <{local}@{domain.domain}>"

    params: resend.Emails.SendParams = {
        "from": from_address,
        "to": [contact.email],
        "subject": draft.subject,
        "text": draft.body,
        "reply_to": settings.zoho_reply_to,
        "headers": {
            "List-Unsubscribe": f"<mailto:{settings.zoho_reply_to}?subject=unsubscribe>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    }

    try:
        result = resend.Emails.send(params)
        message_id = result.get("id")
        _record_success(contact, domain, draft, message_id)
        return SendResult(success=True, resend_message_id=message_id)
    except Exception as exc:
        return SendResult(success=False, error=str(exc))


def _pick_local(domain: SendingDomain) -> str:
    if not domain.from_locals:
        return "hello"
    return random.choice(domain.from_locals)


def _record_success(
    contact: Contact,
    domain: SendingDomain,
    draft: Draft,
    message_id: str | None,
) -> None:
    db = get_db()
    db.table("outreach_emails").insert(
        {
            "contact_id": contact.id,
            "subject": draft.subject,
            "body": draft.body,
            "status": "sent",
            "resend_message_id": message_id,
            "sent_at": "now()",
        }
    ).execute()
    db.table("contacts").update(
        {"status": "sent", "domain_id": domain.id}
    ).eq("id", contact.id).execute()
    domain_module.record_send(domain)
