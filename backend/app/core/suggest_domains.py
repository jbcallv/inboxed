import time
import httpx
from ..config import settings
from .models import DomainSuggestion

_DOMAINR_STATUS_URL = "https://domainr.p.rapidapi.com/v2/status"
_PREFIXES = ["get", "try", "use", "go", "mail"]
_SUFFIXES = ["-hq", "-app", "-team"]
_TLDS = [".io", ".co", ".ai", ".com", ".net"]


def suggest_sending_domains(base_name: str) -> list[DomainSuggestion]:
    if not settings.domainr_api_key:
        return []

    candidates = _build_candidates(base_name)
    results = []
    for domain in candidates:
        suggestion = _check(domain)
        if suggestion and suggestion.available:
            results.append(suggestion)
        time.sleep(0.15)  # ~6 req/s — stays under RapidAPI free tier limits
    return results


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
            _DOMAINR_STATUS_URL,
            params={"domain": domain},
            headers={
                "X-RapidAPI-Key": settings.domainr_api_key,
                "X-RapidAPI-Host": "domainr.p.rapidapi.com",
            },
            timeout=10,
        )
        if response.status_code == 429:
            time.sleep(1)
            response = httpx.get(
                _DOMAINR_STATUS_URL,
                params={"domain": domain},
                headers={
                    "X-RapidAPI-Key": settings.domainr_api_key,
                    "X-RapidAPI-Host": "domainr.p.rapidapi.com",
                },
                timeout=10,
            )
        if response.status_code != 200:
            return None
        for entry in response.json().get("status", []):
            if entry.get("domain") == domain:
                summary = entry.get("summary", "").lower()
                available = "inactive" in summary or "undelegated" in summary
                return DomainSuggestion(domain=domain, available=available)
    except Exception:
        pass
    return None
