import httpx
from ..utils.text import html_to_text, truncate

_MAX_CHARS = 4_000
_EXTRA_PATHS = ["/about", "/contact", "/team"]
_TIMEOUT = 10


def scrape_company(url: str) -> str:
    """Fetches homepage + key subpages, returns cleaned text capped at 4 000 chars."""
    url = _normalise_url(url)
    pages = [url] + [url.rstrip("/") + path for path in _EXTRA_PATHS]
    chunks: list[str] = []
    for page in pages:
        text = _fetch_page(page)
        if text:
            chunks.append(text)
    combined = "\n\n".join(chunks)
    return truncate(combined, _MAX_CHARS)


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
