import logging

import resend

from ..config import settings
from ..db import get_db
from ..utils.email_format import normalize

log = logging.getLogger(__name__)


def is_suppressed(email: str) -> bool:
    db = get_db()
    result = (
        db.table("suppressions")
        .select("id")
        .eq("email", normalize(email))
        .limit(1)
        .execute()
    )
    return len(result.data) > 0


def suppress(email: str, reason: str) -> None:
    """Records the email in our own table and Resend's suppression list, which blocks sending."""
    normalized = normalize(email)
    db = get_db()
    db.table("suppressions").upsert(
        {"email": normalized, "reason": reason},
        on_conflict="email",
    ).execute()
    _suppress_in_resend(normalized)


def _suppress_in_resend(email: str) -> None:
    resend.api_key = settings.resend_api_key
    try:
        resend.Suppressions.add({"email": email})
    except Exception as exc:
        log.error("Resend suppression add failed for %s: %s", email, exc)
