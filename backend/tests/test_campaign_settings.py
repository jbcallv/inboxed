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
    def test_writes_trimmed_address(self):
        db = mock_db()
        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns._assert_owns"),
        ):
            set_campaign_settings(
                "campaign-uuid", CampaignSettingsUpdate(physical_address="  123 Main St  "), USER
            )
        db.update.assert_called_once_with({"physical_address": "123 Main St"})

    def test_blank_address_clears_column(self):
        db = mock_db()
        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns._assert_owns"),
        ):
            set_campaign_settings("campaign-uuid", CampaignSettingsUpdate(physical_address="   "), USER)
        db.update.assert_called_once_with({"physical_address": None})


class TestGenerateContactFooter:
    def test_appends_address_and_unsubscribe_link_to_draft_body(self):
        contact = make_contact(email="alice@acme.com", status="enriched")
        db = mock_db()
        draft = Draft(subject="Hi Alice", body="Quick note about Acme.")

        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns.enrich_module.scrape_company", return_value=""),
            patch("app.api.campaigns.bio_enrich_module.build_narrative_bio", return_value=""),
            patch("app.api.campaigns.generate_module.generate_email", return_value=draft),
            patch("app.api.campaigns._campaign_physical_address", return_value="123 Main St, Austin, TX"),
        ):
            result_contact, warning = _generate_contact(contact)

        inserted_body = db.insert.call_args.args[0]["body"]
        assert "Quick note about Acme." in inserted_body
        assert "123 Main St, Austin, TX" in inserted_body
        assert "email=alice%40acme.com" in inserted_body
        assert warning == ""
        assert result_contact.status == "drafted"

    def test_warns_when_no_physical_address_set(self):
        contact = make_contact(email="alice@acme.com", status="enriched")
        db = mock_db()
        draft = Draft(subject="Hi Alice", body="Quick note about Acme.")

        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns.enrich_module.scrape_company", return_value=""),
            patch("app.api.campaigns.bio_enrich_module.build_narrative_bio", return_value=""),
            patch("app.api.campaigns.generate_module.generate_email", return_value=draft),
            patch("app.api.campaigns._campaign_physical_address", return_value=""),
        ):
            _result_contact, warning = _generate_contact(contact)

        assert "physical address" in warning.lower()
