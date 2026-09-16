import json

import anthropic

from ..config import settings
from .models import Contact, Draft

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def generate_email(
    contact: Contact,
    website_text: str,
    narrative_bio: str = "",
    system_prompt: str = "",
) -> Draft | None:
    """Calls Claude with the campaign prompt. Returns Draft or None on parse failure."""
    user_message = _build_user_message(contact, website_text, narrative_bio)
    client = _get_client()

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": system_prompt or settings.generation_system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text.strip()
    return _parse_draft(raw)


def build_full_prompt(contact: Contact, system_prompt: str, narrative_bio: str = "") -> str:
    system = system_prompt or settings.generation_system_prompt
    user_message = _build_user_message(contact, "", narrative_bio)
    return f"SYSTEM PROMPT\n{system}\n\nUSER MESSAGE\n{user_message}"


def _build_user_message(contact: Contact, website_text: str, narrative_bio: str = "") -> str:
    name = f"{contact.first_name} {contact.last_name}".strip() or contact.company_name or "Unknown"
    parts = [
        f"Prospect: {name}",
        f"Role: {contact.position or 'Unknown'}",
        f"Company: {contact.company_name or 'Unknown'}",
        f"Website: {contact.company_website or 'Unknown'}",
    ]
    if narrative_bio:
        parts.append(f"Profile: {narrative_bio}")
    elif contact.bio:
        parts.append(f"Bio: {contact.bio}")
    if website_text:
        parts.append(f"\nWebsite excerpt:\n{website_text[:2000]}")

    greeting_name = contact.first_name or "there"
    parts.append(
        f'\nReturn JSON only, no markdown. Schema: '
        f'{{"subject": "4-6 words, specific to this company. Just the blurb — '
        f'do not include any company names or a prefix, those are added separately", '
        f'"body": "under 150 words. Start with the greeting \'Hi {greeting_name},\' '
        f'followed by a blank line, then the email. No signature, no sign-off, '
        f'no unsubscribe or footer text after the body."}}'
    )

    return "\n".join(parts)


def format_subject(sender_company_name: str, their_company_name: str, blurb: str) -> str:
    sender = sender_company_name.strip() or "Us"
    theirs = their_company_name.strip() or "You"
    return f"{sender}/{theirs} - {blurb.strip()}"


def _parse_draft(raw: str) -> Draft | None:
    try:
        data = json.loads(_strip_code_fence(raw))
        subject = data.get("subject", "").strip()
        body = data.get("body", "").strip()
        if subject and body:
            return Draft(subject=subject, body=body)
    except (json.JSONDecodeError, AttributeError):
        pass
    return None


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()
