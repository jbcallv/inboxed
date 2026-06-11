from datetime import date
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..db import get_db
from ..core.suggest_domains import suggest_sending_domains
from ..config import settings
from .auth import get_current_user

router = APIRouter(prefix="/domains", tags=["domains"])


class DomainCreate(BaseModel):
    campaign_id: str
    domain: str
    from_name: str
    from_locals: list[str]


class SuggestRequest(BaseModel):
    base_name: str


@router.get("")
def list_domains(campaign_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    domains = (
        db.table("sending_domains")
        .select("*")
        .eq("campaign_id", campaign_id)
        .execute()
        .data
    )
    today = date.today().isoformat()
    domain_ids = [d["id"] for d in domains]
    stats_map: dict = {}
    if domain_ids:
        stats = (
            db.table("domain_daily_stats")
            .select("domain_id,sent_count")
            .eq("date", today)
            .in_("domain_id", domain_ids)
            .execute()
            .data
        )
        stats_map = {s["domain_id"]: s["sent_count"] for s in stats}
    for d in domains:
        d["sent_today"] = stats_map.get(d["id"], 0)
        d["cap_today"] = _warmup_cap(d)
    return domains


@router.post("")
def add_domain(body: DomainCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    result = db.table("sending_domains").insert(
        {
            "campaign_id": body.campaign_id,
            "domain": body.domain,
            "from_name": body.from_name,
            "from_locals": body.from_locals,
            "status": "warming",
            "warmup_started_on": date.today().isoformat(),
        }
    ).execute()
    return result.data[0]


@router.post("/suggest")
def suggest_domains(body: SuggestRequest, user: dict = Depends(get_current_user)):
    suggestions = suggest_sending_domains(body.base_name)
    return [s.model_dump() for s in suggestions]


def _warmup_cap(domain: dict) -> int:
    started = date.fromisoformat(domain["warmup_started_on"])
    day = (date.today() - started).days
    steady = domain.get("steady_cap_override") or settings.warmup_steady_cap
    return min(steady, settings.warmup_start_cap + settings.warmup_step * day)
