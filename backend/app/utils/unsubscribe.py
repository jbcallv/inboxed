from urllib.parse import urlencode

from ..config import settings


def unsubscribe_url(email: str, campaign_id: str) -> str:
    query = urlencode({"email": email, "campaign": campaign_id})
    return f"{settings.frontend_url}/unsubscribe?{query}"


def build_compliance_footer(physical_address: str | None, email: str, campaign_id: str) -> str:
    address_line = physical_address.strip() if physical_address else ""
    lines = ["\n\n---"]
    if address_line:
        lines.append(address_line)
    lines.append(f"Unsubscribe: {unsubscribe_url(email, campaign_id)}")
    return "\n".join(lines)
