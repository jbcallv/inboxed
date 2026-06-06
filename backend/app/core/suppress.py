from ..db import get_db
from ..utils.email_format import normalize


def is_suppressed(email: str) -> bool:
    db = get_db()
    result = (
        db.table("suppressions")
        .select("id")
        .eq("email", normalize(email))
        .limit(1)
        .execute()
    )
    return len(result.data) > 0


def suppress(email: str, reason: str) -> None:
    db = get_db()
    db.table("suppressions").upsert(
        {"email": normalize(email), "reason": reason},
        on_conflict="email",
    ).execute()
