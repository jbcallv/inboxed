from datetime import date
from ..db import get_db
from ..config import settings
from ..core.models import SendingDomain
from ..core.domains import cap_today


def reset_daily_counts() -> None:
    """
    Runs at local midnight. Advances domain statuses from 'warming' to 'active'
    for any domain that has reached steady cap. (Stats reset is automatic — each
    day gets its own domain_daily_stats row.)
    """
    db = get_db()
    warming = (
        db.table("sending_domains")
        .select("*")
        .eq("status", "warming")
        .execute()
    )
    for row in warming.data:
        domain = SendingDomain(**row)
        if cap_today(domain) >= _steady_cap(domain):
            db.table("sending_domains").update({"status": "active"}).eq(
                "id", domain.id
            ).execute()


def _steady_cap(domain: SendingDomain) -> int:
    if domain.steady_cap_override is not None:
        return domain.steady_cap_override
    return settings.warmup_steady_cap
