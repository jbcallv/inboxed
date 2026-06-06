import httpx
from ..config import settings

_HUNTER_URL = "https://api.hunter.io/v2/email-finder"


def find_email(first: str, last: str, domain: str) -> str | None:
    """
    Uses Hunter email-finder. Returns the email string if found with
    sufficient confidence, None otherwise. No pattern-guessing — if
    Hunter returns nothing, the caller marks the contact no_email.
    """
    if not settings.hunter_api_key:
        return None

    response = httpx.get(
        _HUNTER_URL,
        params={
            "first_name": first,
            "last_name": last,
            "domain": domain,
            "api_key": settings.hunter_api_key,
        },
        timeout=15,
    )

    if response.status_code in (404, 429):
        return None

    response.raise_for_status()
    data = response.json().get("data", {})
    return data.get("email")
