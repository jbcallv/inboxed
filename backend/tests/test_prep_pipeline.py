"""
Tests for the contact prep pipeline (_process_contact) and campaign API endpoints.
Covers the main happy path, no-email drop, verification failure, and generation failure.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.api.campaigns import _process_contact
from app.core.models import Contact, Draft
from .conftest import make_contact, mock_db


def _db_with_contact(contact_row: dict) -> MagicMock:
    db = mock_db()
    db.execute.return_value = MagicMock(data=[contact_row])
    return db


class TestProcessContactHappyPath:
    def test_contact_with_email_reaches_drafted(self):
        contact = make_contact(email="alice@acme.com", status="new")
        db = mock_db()
        draft = Draft(subject="Hi Alice", body="Quick note…")

        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns.verify_module.verify_contact",
                  return_value=contact.model_copy(update={"status": "verified"})),
            patch("app.api.campaigns.enrich_module.scrape_company", return_value="Acme builds widgets."),
            patch("app.api.campaigns.generate_module.generate_email", return_value=draft),
        ):
            result_contact, warning = _process_contact(contact, skip_verification=False)

        assert result_contact.status == "drafted"
        assert warning == ""

    def test_skip_verification_bypasses_mv(self):
        contact = make_contact(email="bob@corp.com", status="new")
        db = mock_db()
        draft = Draft(subject="Hi Bob", body="Short email.")

        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns.verify_module.verify_contact") as mock_verify,
            patch("app.api.campaigns.enrich_module.scrape_company", return_value=""),
            patch("app.api.campaigns.generate_module.generate_email", return_value=draft),
        ):
            result_contact, warning = _process_contact(contact, skip_verification=True)

        mock_verify.assert_not_called()
        assert result_contact.status == "drafted"


class TestProcessContactNoEmail:
    def test_drops_contact_when_hunter_finds_nothing(self):
        contact = make_contact(email=None, status="new")
        db = mock_db()

        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns.finder_module.find_email", return_value=(None, "not_found")),
        ):
            result_contact, warning = _process_contact(contact, skip_verification=True)

        assert result_contact.status == "no_email"

    def test_uses_hunter_email_and_continues(self):
        contact = make_contact(email=None, status="new")
        db = mock_db()
        draft = Draft(subject="Hi", body="Body.")

        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns.finder_module.find_email", return_value=("found@corp.com", "found")),
            patch("app.api.campaigns.enrich_module.scrape_company", return_value=""),
            patch("app.api.campaigns.generate_module.generate_email", return_value=draft),
        ):
            result_contact, warning = _process_contact(contact, skip_verification=True)

        assert result_contact.status == "drafted"


class TestProcessContactVerificationFailures:
    def test_rejected_contact_stops_pipeline(self):
        contact = make_contact(email="bad@spam.com", status="new")
        db = mock_db()

        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns.verify_module.verify_contact",
                  return_value=contact.model_copy(update={"status": "rejected"})),
            patch("app.api.campaigns.generate_module.generate_email") as mock_gen,
        ):
            result_contact, warning = _process_contact(contact, skip_verification=False)

        mock_gen.assert_not_called()
        assert result_contact.status == "rejected"

    def test_mv_no_credits_surfaces_warning(self):
        contact = make_contact(email="ok@corp.com", status="new")
        db = mock_db()

        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns.verify_module.verify_contact",
                  side_effect=Exception("Insufficient credits")),
        ):
            result_contact, warning = _process_contact(contact, skip_verification=False)

        assert "credits" in warning.lower()
        assert result_contact.status == "new"


class TestProcessContactGenerationFailure:
    def test_generation_failure_leaves_contact_in_generating(self):
        contact = make_contact(email="ok@corp.com", status="new")
        db = mock_db()

        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns.verify_module.verify_contact",
                  return_value=contact.model_copy(update={"status": "verified"})),
            patch("app.api.campaigns.enrich_module.scrape_company", return_value=""),
            patch("app.api.campaigns.generate_module.generate_email", return_value=None),
        ):
            result_contact, warning = _process_contact(contact, skip_verification=False)

        assert result_contact.status == "generating"
