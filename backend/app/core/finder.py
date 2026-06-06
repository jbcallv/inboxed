import time
import httpx
from ..config import settings

_HUNTER_URL = "https://api.hunter.io/v2/email-finder"
_RETRY_SLEEP = 2


def find_email(first: str, last: str, domain: str) -> tuple[str | None, str]:
    """
    Uses Hunter email-finder. Returns (email, reject_reason).
    reject_reason is one of: "" (found), "not_found", "rate_limited", "no_key".
    No pattern-guessing — if Hunter returns nothing, caller marks contact no_email.
    """
    if not settings.hunter_api_key:
        return None, "no_key"
    if not domain:
        return None, "no_domain"

    result, reason = _call_hunter(first, last, domain)
    if reason == "rate_limited":
        time.sleep(_RETRY_SLEEP)
        result, reason = _call_hunter(first, last, domain)

    return result, reason


def _call_hunter(first: str, last: str, domain: str) -> tuple[str | None, str]:
    try:
        response = httpx.get(
            _HUNTER_URL,
            params={"first_name": first, "last_name": last, "domain": domain, "api_key": settings.hunter_api_key},
            timeout=15,
        )
    except Exception:
        return None, "not_found"

    if response.status_code == 429:
        return None, "rate_limited"
    if response.status_code == 404:
        return None, "not_found"
    if not response.is_success:
        return None, "not_found"

    email = response.json().get("data", {}).get("email")
    return (email, "") if email else (None, "not_found")
