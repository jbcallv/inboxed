from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class Contact(BaseModel):
    id: int
    campaign_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    position: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None
    status: str
    mv_result: Optional[str] = None
    reject_reason: Optional[str] = None
    domain_id: Optional[str] = None


class SendingDomain(BaseModel):
    id: str
    domain: str
    from_name: str
    from_locals: list[str]
    status: str
    warmup_started_on: date
    steady_cap_override: Optional[int] = None


class Draft(BaseModel):
    subject: str
    body: str


class VerifyResult(BaseModel):
    email: str
    code: str  # ok | catch_all | disposable | invalid | unknown


class SendResult(BaseModel):
    success: bool
    resend_message_id: Optional[str] = None
    error: Optional[str] = None


class RawReply(BaseModel):
    imap_uid: str
    from_email: str
    body: str
    received_at: datetime


class DomainSuggestion(BaseModel):
    domain: str
    available: bool
