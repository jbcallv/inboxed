from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


GENERATION_SYSTEM_PROMPT = """\
You are an expert B2B sales copywriter specializing in AI integration for enterprises.
Your job is to write concise, hyper-personalized cold outreach emails (under 150 words total).

The sender's company helps businesses identify and solve specific AI integration gaps — from
automating manual workflows, to building AI-powered customer experiences, to integrating LLMs
into existing products.

Rules:
- Never use generic AI buzzwords like "leverage", "revolutionize", "transform", "game-changer"
- Reference something specific about the prospect's actual role, company, or bio
- Identify a concrete, plausible AI pain point for their specific context
- Keep paragraphs to 1-2 sentences each
- End with a single soft CTA (e.g. "Would a 20-minute call make sense?")
- Return only valid JSON, no markdown wrapping"""

UNSUBSCRIBE_FOOTER = (
    "\n\n---\nIf you'd prefer not to hear from us, "
    "simply reply with \"unsubscribe\" and we'll remove you immediately."
)


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""

    anthropic_api_key: str = ""
    millionverifier_api_key: str = ""
    hunter_api_key: str = ""
    resend_api_key: str = ""
    resend_webhook_secret: str = ""

    zoho_imap_host: str = "imap.zoho.com"
    zoho_imap_user: str = ""
    zoho_imap_password: str = ""
    zoho_reply_to: str = ""

    domainr_api_key: Optional[str] = None

    send_window_start: int = 8
    send_window_end: int = 18
    send_timezone: str = "America/New_York"

    warmup_start_cap: int = 20
    warmup_step: int = 25
    warmup_steady_cap: int = 250
    max_bounce_rate: float = 0.03
    max_complaint_rate: float = 0.0005

    prep_workers: int = 20  # parallel contacts during prep pipeline

    generation_system_prompt: str = GENERATION_SYSTEM_PROMPT

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
