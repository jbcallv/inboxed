import time
import httpx
from ..config import settings
from .models import DomainSuggestion

_RDAP_URL = "https://rdap.org/domain/{domain}"
_PREFIXES = ["get", "try", "use", "go", "mail"]
_SUFFIXES = ["-hq", "-app", "-team"]
_TLDS = [".io", ".co", ".ai", ".com", ".net"]


def suggest_sending_domains(base_name: str) -> list[DomainSuggestion]:
    candidates = _build_candidates(base_name)
    results = []
    for domain in candidates:
        suggestion = _check_rdap(domain)
        if suggestion and suggestion.available:
            results.append(suggestion)
        time.sleep(0.1)
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


def _check_rdap(domain: str) -> DomainSuggestion | None:
    try:
        response = httpx.get(
            _RDAP_URL.format(domain=domain),
            timeout=8,
            follow_redirects=True,
        )
        # 404 = not registered = available; 200 = taken
        print(response)
        available = response.status_code == 404
        return DomainSuggestion(domain=domain, available=available)
    except Exception:
        return None
