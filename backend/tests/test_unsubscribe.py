from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.unsubscribe import UnsubscribeRequest, unsubscribe
from app.utils.unsubscribe import build_compliance_footer, unsubscribe_url

from .conftest import mock_db


class TestUnsubscribeUrl:
    def test_encodes_email_and_campaign(self):
        url = unsubscribe_url("alice@acme.com", "campaign-uuid")
        assert "email=alice%40acme.com" in url
        assert "campaign=campaign-uuid" in url
        assert url.startswith("http")


class TestBuildComplianceFooter:
    def test_includes_address_and_link(self):
        footer = build_compliance_footer("123 Main St, Austin, TX", "alice@acme.com", "campaign-uuid")
        assert "123 Main St, Austin, TX" in footer
        assert "Unsubscribe:" in footer
        assert "email=alice%40acme.com" in footer

    def test_omits_address_line_when_blank(self):
        footer = build_compliance_footer("", "alice@acme.com", "campaign-uuid")
        assert "Unsubscribe:" in footer
        assert footer.strip().splitlines() == ["---", "Unsubscribe: " + unsubscribe_url("alice@acme.com", "campaign-uuid")]


class TestUnsubscribeEndpoint:
    def test_suppresses_and_marks_contact(self):
        db = mock_db()
        db.execute.return_value = MagicMock(data=[{"id": 1}])
        with (
            patch("app.api.unsubscribe.get_db", return_value=db),
            patch("app.api.unsubscribe.suppress_module.suppress") as mock_suppress,
        ):
            result = unsubscribe(UnsubscribeRequest(email="Alice@Acme.com", campaign_id="campaign-uuid"))

        mock_suppress.assert_called_once_with("alice@acme.com", "unsubscribe")
        db.update.assert_called_once_with({"status": "unsubscribed"})
        assert result == {"status": "unsubscribed"}

    def test_404_when_contact_not_found(self):
        db = mock_db()
        db.execute.return_value = MagicMock(data=[])
        with patch("app.api.unsubscribe.get_db", return_value=db), pytest.raises(HTTPException) as exc:
            unsubscribe(UnsubscribeRequest(email="ghost@nowhere.com", campaign_id="campaign-uuid"))
        assert exc.value.status_code == 404
