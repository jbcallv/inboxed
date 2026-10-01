from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.domains import DomainCreate, add_domain

from .conftest import mock_db

USER = {"sub": "user-uuid"}
NEW_DOMAIN = DomainCreate(
    campaign_id="new-campaign",
    domain="shared.com",
    from_name="Joseph",
    from_locals=["joseph"],
)


def _add_with_existing_rows(existing_rows: list[dict]) -> MagicMock:
    db = mock_db()
    db.execute.side_effect = [MagicMock(data=existing_rows), MagicMock(data=[{"id": "row"}])]
    with patch("app.api.domains.get_db", return_value=db):
        add_domain(NEW_DOMAIN, USER)
    return db


class TestAddDomain:
    def test_new_domain_starts_warming_today(self):
        db = _add_with_existing_rows([])
        inserted = db.insert.call_args.args[0]
        assert inserted["status"] == "warming"
        assert inserted["warmup_started_on"] == date.today().isoformat()
        assert inserted["campaign_id"] == "new-campaign"

    def test_domain_on_another_campaign_keeps_its_warmup_progress(self):
        db = _add_with_existing_rows(
            [
                {
                    "campaign_id": "old-campaign",
                    "status": "active",
                    "warmup_started_on": "2026-08-01",
                    "steady_cap_override": 100,
                }
            ]
        )
        inserted = db.insert.call_args.args[0]
        assert inserted["status"] == "active"
        assert inserted["warmup_started_on"] == "2026-08-01"
        assert inserted["steady_cap_override"] == 100
        assert inserted["from_name"] == "Joseph"

    def test_domain_already_on_this_campaign_is_rejected(self):
        db = mock_db()
        db.execute.return_value = MagicMock(
            data=[
                {
                    "campaign_id": "new-campaign",
                    "status": "active",
                    "warmup_started_on": "2026-08-01",
                    "steady_cap_override": None,
                }
            ]
        )
        with patch("app.api.domains.get_db", return_value=db), pytest.raises(HTTPException) as error:
            add_domain(NEW_DOMAIN, USER)
        assert error.value.status_code == 409
        db.insert.assert_not_called()
