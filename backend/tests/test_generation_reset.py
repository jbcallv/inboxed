from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api import campaigns
from app.api.campaigns import reset_generation
from .conftest import mock_db

USER = {"sub": "user-uuid"}


class TestResetGeneration:
    def test_clears_drafts_and_rolls_contacts_back(self):
        db = mock_db()
        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns._assert_owns"),
            patch("app.api.campaigns._delete_draft_emails", return_value=7) as delete_drafts,
            patch("app.api.campaigns._bulk_status_update") as bulk_update,
        ):
            result = reset_generation("campaign-uuid", USER)

        assert result == {"cleared_emails": 7}
        delete_drafts.assert_called_once_with(db, "campaign-uuid")
        rolled_back = {call.kwargs["from_status"] for call in bulk_update.call_args_list}
        assert rolled_back == set(campaigns._GENERATED_STATUSES)
        assert all(call.kwargs["to_status"] == "verified" for call in bulk_update.call_args_list)
        db.update.assert_called_once_with({"status": "verified"})

    def test_rejects_when_not_owner(self):
        with patch(
            "app.api.campaigns._assert_owns",
            side_effect=HTTPException(404, "Campaign not found"),
        ):
            with pytest.raises(HTTPException) as exc:
                reset_generation("campaign-uuid", USER)
        assert exc.value.status_code == 404


class TestDeleteDraftEmails:
    def test_deletes_only_draft_rows_for_campaign_contacts(self):
        db = MagicMock()
        db.table.return_value = db
        db.select.return_value = db
        db.eq.return_value = db
        db.in_.return_value = db
        db.order.return_value = db
        db.range.return_value = db
        db.delete.return_value = db
        db.execute.side_effect = [
            MagicMock(data=[{"id": 1}, {"id": 2}, {"id": 3}]),
            MagicMock(data=[{"id": 10}, {"id": 11}]),
        ]

        deleted = campaigns._delete_draft_emails(db, "campaign-uuid")

        assert deleted == 2
        db.delete.assert_called_once()
        db.in_.assert_called_once_with("contact_id", [1, 2, 3])
        db.eq.assert_any_call("status", "draft")
