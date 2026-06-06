import httpx
from ..config import settings
from .models import DomainSuggestion

_DOMAINR_URL = "https://domainr.p.rapidapi.com/v2/search"
_PREFIXES = ["get", "try", "use", "go", "mail"]
_SUFFIXES = ["-hq", "-app", "-team"]
_TLDS = [".io", ".co", ".ai", ".com", ".net"]


def suggest_sending_domains(base_name: str) -> list[DomainSuggestion]:
    """Returns available domain suggestions for base_name. Empty if DOMAINR_API_KEY unset."""
    if not settings.domainr_api_key:
        return []

    candidates = _build_candidates(base_name)
    return [s for s in [_check(d) for d in candidates] if s is not None and s.available]


def _build_candidates(base: str) -> list[str]:
    base = base.lower().replace(" ", "")
    candidates = []
    for prefix in _PREFIXES:
        for tld in _TLDS:
            candidates.append(f"{prefix}{base}{tld}")
    for suffix in _SUFFIXES:
        for tld in _TLDS:
            candidates.append(f"{base}{suffix}{tld}")
    for tld in _TLDS[1:]:
        candidates.append(f"{base}{tld}")
    return list(dict.fromkeys(candidates))[:20]


def _check(domain: str) -> DomainSuggestion | None:
    try:
        response = httpx.get(
            _DOMAINR_URL,
            params={"query": domain},
            headers={
                "X-RapidAPI-Key": settings.domainr_api_key,
                "X-RapidAPI-Host": "domainr.p.rapidapi.com",
            },
            timeout=10,
        )
        if response.status_code != 200:
            return None
        results = response.json().get("results", [])
        for r in results:
            if r.get("domain") == domain:
                available = "inactive" in r.get("summary", "").lower()
                return DomainSuggestion(domain=domain, available=available)
    except Exception:
        pass
    return None
