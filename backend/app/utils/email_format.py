import re

_ROLE_PREFIXES = frozenset({
    "info", "sales", "support", "admin", "hello", "team", "noreply", "no-reply",
    "webmaster", "postmaster", "marketing", "contact", "help", "billing",
    "accounts", "office", "enquiries", "enquiry", "hr", "pr", "media",
    "legal", "privacy", "security", "abuse", "hostmaster", "usenet",
    "news", "uucp", "ftp", "jobs", "careers",
})

_DISPOSABLE_DOMAINS = frozenset({
    "mailinator.com", "guerrillamail.com", "guerrillamail.net", "guerrillamail.org",
    "guerrillamail.biz", "guerrillamail.de", "guerrillamail.info",
    "throwam.com", "throwaway.email", "tempr.email", "yopmail.com",
    "yopmail.fr", "cool.fr.nf", "jetable.fr.nf", "nospam.ze.tc",
    "nomail.xl.cx", "mega.zik.dj", "speed.1s.fr", "courriel.fr.nf",
    "moncourrier.fr.nf", "monemail.fr.nf", "monmail.fr.nf",
    "trashmail.com", "trashmail.at", "trashmail.io", "trashmail.me",
    "trashmail.net", "trashmail.org", "dispostable.com", "mailnull.com",
    "spamgourmet.com", "sharklasers.com", "guerrillamailblock.com",
    "grr.la", "guerrillamail.info", "spam4.me", "maildrop.cc",
    "getairmail.com", "filzmail.com", "tempinbox.com",
    "fakeinbox.com", "mailnesia.com", "mailnull.com",
    "spambox.us", "spaml.com", "discard.email",
})

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


def is_valid_syntax(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


def is_role_address(email: str) -> bool:
    local = email.split("@")[0].lower()
    return local in _ROLE_PREFIXES


def is_disposable(email: str) -> bool:
    domain = email.split("@")[-1].lower()
    return domain in _DISPOSABLE_DOMAINS


def normalize(email: str) -> str:
    return email.strip().lower()


def is_acceptable_format(email: str) -> tuple[bool, str]:
    """Returns (ok, reason). reason is empty string when ok."""
    email = normalize(email)
    if not is_valid_syntax(email):
        return False, "invalid_syntax"
    if is_role_address(email):
        return False, "role_address"
    if is_disposable(email):
        return False, "disposable_domain"
    return True, ""


def dedupe(emails: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for email in emails:
        normalized = normalize(email)
        if normalized not in seen:
            seen.add(normalized)
            result.append(email)
    return result
