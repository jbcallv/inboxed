from unittest.mock import patch

from app.api.campaigns import (
    CampaignSettingsUpdate,
    _generate_contact,
    set_campaign_settings,
)
from app.core.models import Draft

from .conftest import make_contact, mock_db

USER = {"sub": "user-uuid"}


class TestSetCampaignSettings:
    def test_writes_trimmed_fields(self):
        db = mock_db()
        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns._assert_owns"),
        ):
            set_campaign_settings(
                "campaign-uuid",
                CampaignSettingsUpdate(physical_address="  123 Main St  ", sender_company_name="  Acme Inc  "),
                USER,
            )
        db.update.assert_called_once_with(
            {"physical_address": "123 Main St", "sender_company_name": "Acme Inc"}
        )

    def test_blank_fields_clear_columns(self):
        db = mock_db()
        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns._assert_owns"),
        ):
            set_campaign_settings(
                "campaign-uuid",
                CampaignSettingsUpdate(physical_address="   ", sender_company_name="   "),
                USER,
            )
        db.update.assert_called_once_with({"physical_address": None, "sender_company_name": None})


class TestGenerateContactFooterAndSubject:
    def test_appends_footer_and_prefixes_subject(self):
        contact = make_contact(email="alice@acme.com", company_name="Acme Corp", status="enriched")
        db = mock_db()
        draft = Draft(subject="Cut reporting time in half", body="Quick note about Acme.")

        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns.enrich_module.scrape_company", return_value=""),
            patch("app.api.campaigns.bio_enrich_module.build_narrative_bio", return_value=""),
            patch("app.api.campaigns.generate_module.generate_email", return_value=draft),
            patch(
                "app.api.campaigns._campaign_settings",
                return_value={"physical_address": "123 Main St, Austin, TX", "sender_company_name": "Inboxed"},
            ),
        ):
            result_contact, warning = _generate_contact(contact)

        inserted = db.insert.call_args.args[0]
        assert inserted["subject"] == "Inboxed/Acme Corp - Cut reporting time in half"
        assert "Quick note about Acme." in inserted["body"]
        assert "123 Main St, Austin, TX" in inserted["body"]
        assert "email=alice%40acme.com" in inserted["body"]
        assert warning == ""
        assert result_contact.status == "drafted"

    def test_warns_when_settings_missing(self):
        contact = make_contact(email="alice@acme.com", status="enriched")
        db = mock_db()
        draft = Draft(subject="Cut reporting time in half", body="Quick note about Acme.")

        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns.enrich_module.scrape_company", return_value=""),
            patch("app.api.campaigns.bio_enrich_module.build_narrative_bio", return_value=""),
            patch("app.api.campaigns.generate_module.generate_email", return_value=draft),
            patch("app.api.campaigns._campaign_settings", return_value={}),
        ):
            _result_contact, warning = _generate_contact(contact)

        assert "physical address" in warning.lower()
        assert "sender company name" in warning.lower()
