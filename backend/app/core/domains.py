from datetime import date
from ..db import get_db
from ..config import settings
from .models import SendingDomain


def active_domains(campaign_id: str | None = None) -> list[SendingDomain]:
    db = get_db()
    q = db.table("sending_domains").select("*").in_("status", ["warming", "active"])
    if campaign_id:
        q = q.eq("campaign_id", campaign_id)
    return [SendingDomain(**row) for row in q.execute().data]


def cap_today(domain: SendingDomain) -> int:
    day = (date.today() - domain.warmup_started_on).days
    if domain.steady_cap_override is not None:
        steady = domain.steady_cap_override
    else:
        steady = settings.warmup_steady_cap
    return min(steady, settings.warmup_start_cap + settings.warmup_step * day)


def remaining_today(domain: SendingDomain) -> int:
    sent = _sent_today(domain)
    return max(0, cap_today(domain) - sent)


def pick_domain(domains: list[SendingDomain]) -> SendingDomain | None:
    """Returns the domain with the most remaining capacity today."""
    candidates = [(remaining_today(d), d) for d in domains]
    candidates = [(r, d) for r, d in candidates if r > 0]
    if not candidates:
        return None
    return max(candidates, key=lambda x: x[0])[1]


def record_send(domain: SendingDomain) -> None:
    db = get_db()
    db.rpc("increment_domain_stat", {"p_domain_id": domain.id, "p_column": "sent_count"}).execute()


def record_bounce(domain_id: str) -> None:
    db = get_db()
    db.rpc("increment_domain_stat", {"p_domain_id": domain_id, "p_column": "bounce_count"}).execute()


def record_complaint(domain_id: str) -> None:
    db = get_db()
    db.rpc("increment_domain_stat", {"p_domain_id": domain_id, "p_column": "complaint_count"}).execute()


def check_and_pause_domains() -> None:
    """Auto-pause any domain exceeding rolling 3-day bounce or complaint rates.
    Also pauses the campaign if all its domains are now paused."""
    db = get_db()
    domains_result = db.table("sending_domains").select("id,domain,status,campaign_id").execute()
    for row in domains_result.data:
        if row["status"] == "paused":
            continue
        _check_domain_rates(db, row["id"])

    # Re-fetch to see updated statuses, then pause campaigns with no active domains
    domains_result = db.table("sending_domains").select("id,status,campaign_id").execute()
    from itertools import groupby
    by_campaign: dict[str, list] = {}
    for row in domains_result.data:
        cid = row.get("campaign_id")
        if cid:
            by_campaign.setdefault(cid, []).append(row["status"])
    for campaign_id, statuses in by_campaign.items():
        if all(s == "paused" for s in statuses):
            db.table("campaigns").update({"status": "paused"}).eq(
                "id", campaign_id
            ).eq("status", "sending").execute()


def _check_domain_rates(db, domain_id: str) -> None:
    result = db.table("domain_daily_stats").select(
        "sent_count,bounce_count,complaint_count"
    ).eq("domain_id", domain_id).order("date", desc=True).limit(3).execute()

    rows = result.data
    if not rows:
        return

    total_sent = sum(r["sent_count"] for r in rows)
    if total_sent < settings.min_sends_before_pause:
        return

    bounce_rate = sum(r["bounce_count"] for r in rows) / total_sent
    complaint_rate = sum(r["complaint_count"] for r in rows) / total_sent

    if bounce_rate > settings.max_bounce_rate or complaint_rate > settings.max_complaint_rate:
        db.table("sending_domains").update({"status": "paused"}).eq("id", domain_id).execute()


def _sent_today(domain: SendingDomain) -> int:
    db = get_db()
    result = (
        db.table("domain_daily_stats")
        .select("sent_count")
        .eq("domain_id", domain.id)
        .eq("date", date.today().isoformat())
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["sent_count"]
    return 0
