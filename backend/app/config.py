from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

from .prompts import DEFAULT_GENERATION_PROMPT


class Settings(BaseSettings):
    frontend_url: str = "http://localhost:5173"

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
    min_sends_before_pause: int = 100

    prep_workers: int = 50  # parallel contacts during prep pipeline

    generation_system_prompt: str = DEFAULT_GENERATION_PROMPT

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
