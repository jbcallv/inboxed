import httpx
from ..config import settings
from ..db import get_db
from ..utils.email_format import is_acceptable_format
from .models import Contact, VerifyResult
from . import suppress as suppress_module

_MV_URL = "https://api.millionverifier.com/api/v3/"


def verify_email(email: str) -> VerifyResult:
    """One real-time MillionVerifier API call."""
    response = httpx.get(
        _MV_URL,
        params={"api": settings.millionverifier_api_key, "email": email},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    return VerifyResult(email=email, code=data.get("result", "unknown"))


def is_deliverable(result: VerifyResult) -> bool:
    return result.code in ("ok", "catch_all")


def verify_contact(contact: Contact) -> Contact:
    """
    Prefilters locally, checks suppression, then calls MillionVerifier.
    Writes result back to DB and returns the updated contact.
    """
    db = get_db()

    ok, reason = is_acceptable_format(contact.email or "")
    if not ok:
        return _reject(db, contact, reason)

    if suppress_module.is_suppressed(contact.email):
        return _reject(db, contact, "suppressed")

    result = verify_email(contact.email)

    if not is_deliverable(result):
        return _reject(db, contact, result.code, mv_result=result.code)

    db.table("contacts").update(
        {"status": "verified", "mv_result": result.code}
    ).eq("id", contact.id).execute()

    return contact.model_copy(update={"status": "verified", "mv_result": result.code})


def _reject(db, contact: Contact, reason: str, mv_result: str | None = None) -> Contact:
    update: dict = {"status": "rejected", "reject_reason": reason}
    if mv_result:
        update["mv_result"] = mv_result
    db.table("contacts").update(update).eq("id", contact.id).execute()
    return contact.model_copy(update={**update})
