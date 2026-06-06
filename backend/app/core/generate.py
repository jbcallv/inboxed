import json
import anthropic
from ..config import settings, UNSUBSCRIBE_FOOTER
from .models import Contact, Draft

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def generate_email(contact: Contact, website_text: str) -> Draft | None:
    """Calls Claude with the proven prompt. Returns Draft or None on parse failure."""
    user_message = _build_user_message(contact, website_text)
    client = _get_client()

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": settings.generation_system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text.strip()
    return _parse_draft(raw)


def _build_user_message(contact: Contact, website_text: str) -> str:
    parts = [
        f"Prospect: {contact.first_name} {contact.last_name}",
        f"Role: {contact.position or 'Unknown'}",
        f"Company: {contact.company_name or 'Unknown'}",
        f"Website: {contact.company_website or 'Unknown'}",
    ]
    if contact.bio:
        parts.append(f"Bio: {contact.bio}")
    if website_text:
        parts.append(f"\nWebsite excerpt:\n{website_text[:2000]}")
    parts.append(
        '\nReturn JSON only: {"subject": "under 8 words, personalized", '
        '"body": "3 short paragraphs under 150 words"}'
    )
    return "\n".join(parts)


def _parse_draft(raw: str) -> Draft | None:
    try:
        data = json.loads(raw)
        subject = data.get("subject", "").strip()
        body = data.get("body", "").strip() + UNSUBSCRIBE_FOOTER
        if subject and body:
            return Draft(subject=subject, body=body)
    except (json.JSONDecodeError, AttributeError):
        pass
    return None
