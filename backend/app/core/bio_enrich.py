import anthropic
from ..config import settings
from .models import Contact

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def build_narrative_bio(contact: Contact) -> str:
    """Uses Haiku to turn structured contact data into a 2-sentence narrative bio."""
    if not contact.bio and not contact.company_name:
        return ""

    name_part = f"{contact.first_name} {contact.last_name}".strip()
    role_part = contact.position or ""
    company_part = contact.company_name or ""
    structured = contact.bio or ""

    if name_part and role_part:
        header = f"Contact: {name_part}, {role_part} at {company_part}"
    elif name_part:
        header = f"Contact: {name_part} at {company_part}"
    else:
        header = f"Company: {company_part}"

    prompt = (
        f"{header}\n"
        f"Data: {structured}\n\n"
        "Write 2 sentences summarizing only what the data above explicitly states. "
        "Do not invent, infer, or add any details not present in the data. "
        "No generic phrases like 'personalized service', 'reliable', 'dedicated', or 'committed'. "
        "If a fact is not in the data, do not mention it. Plain prose, no headers, no bullet points."
    )

    try:
        msg = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return structured
