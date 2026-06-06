from datetime import date
from unittest.mock import MagicMock
import pytest
from app.core.models import Contact, SendingDomain


def make_contact(**kwargs) -> Contact:
    defaults = dict(
        id=1,
        campaign_id="campaign-uuid",
        first_name="Alice",
        last_name="Smith",
        company_name="Acme Corp",
        company_website="https://acme.com",
        position="CTO",
        bio="Loves Python",
        email="alice@acme.com",
        status="new",
        mv_result=None,
        reject_reason=None,
        domain_id=None,
    )
    defaults.update(kwargs)
    return Contact(**defaults)


def make_domain(**kwargs) -> SendingDomain:
    defaults = dict(
        id="domain-uuid",
        domain="getinboxed.com",
        from_name="Joseph",
        from_locals=["joseph", "hello"],
        status="active",
        warmup_started_on=date(2024, 1, 1),
        steady_cap_override=None,
    )
    defaults.update(kwargs)
    return SendingDomain(**defaults)


def mock_db() -> MagicMock:
    db = MagicMock()
    db.table.return_value = db
    db.select.return_value = db
    db.eq.return_value = db
    db.in_.return_value = db
    db.limit.return_value = db
    db.order.return_value = db
    db.update.return_value = db
    db.insert.return_value = db
    db.upsert.return_value = db
    db.rpc.return_value = db
    db.execute.return_value = MagicMock(data=[])
    return db
