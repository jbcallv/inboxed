import httpx
from ..utils.text import html_to_text, truncate

_MAX_CHARS = 2_000
_TIMEOUT = 5


def scrape_company(url: str) -> str:
    """Fetches homepage only, returns cleaned text capped at 2,000 chars."""
    url = _normalise_url(url)
    text = _fetch_page(url)
    return truncate(text, _MAX_CHARS)


def _fetch_page(url: str) -> str:
    try:
        response = httpx.get(url, timeout=_TIMEOUT, follow_redirects=True)
        if response.status_code == 200:
            return html_to_text(response.text)
    except Exception:
        pass
    return ""


def _normalise_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url
