import time
import random
import logging
from ..db import get_db
from ..core.models import Contact, Draft
from ..core.domains import active_domains, remaining_today, check_and_pause_domains
from ..core.send import send_one
from ..utils.time_window import within_send_window

log = logging.getLogger(__name__)

_JITTER_MIN = 8
_JITTER_MAX = 45


def tick() -> None:
    if not within_send_window():
        return

    for campaign_id in _sending_campaign_ids():
        for domain in active_domains(campaign_id):
            budget = remaining_today(domain)
            if budget <= 0:
                continue

            contacts = claim_queued(budget, campaign_id)
            for contact in contacts:
                draft = draft_for(contact)
                if draft is None:
                    _mark_failed(contact)
                    continue

                result = send_one(domain, contact, draft)
                if not result.success:
                    log.warning("Send failed for contact %s: %s", contact.id, result.error)
                    _mark_failed(contact)

                time.sleep(jitter())

    check_and_pause_domains()


def _sending_campaign_ids() -> list[str]:
    db = get_db()
    result = db.table("campaigns").select("id").eq("status", "sending").execute()
    return [row["id"] for row in result.data]


def claim_queued(budget: int, campaign_id: str | None = None) -> list[Contact]:
    db = get_db()
    params: dict = {"p_budget": budget}
    if campaign_id:
        params["p_campaign_id"] = campaign_id
    result = db.rpc("claim_queued_contacts", params).execute()
    return [Contact(**row) for row in result.data]


def draft_for(contact: Contact) -> Draft | None:
    db = get_db()
    result = (
        db.table("outreach_emails")
        .select("subject,body")
        .eq("contact_id", contact.id)
        .eq("status", "draft")
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    row = result.data[0]
    return Draft(subject=row["subject"], body=row["body"])


def _mark_failed(contact: Contact) -> None:
    db = get_db()
    db.table("contacts").update({"status": "queued"}).eq("id", contact.id).execute()


def jitter() -> float:
    return random.uniform(_JITTER_MIN, _JITTER_MAX)
