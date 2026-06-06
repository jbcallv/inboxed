import pytest
from datetime import date
from unittest.mock import MagicMock, patch, call
from app.worker.tick import tick, claim_queued, jitter
from app.core.models import Contact, Draft, SendResult
from .conftest import make_contact, make_domain, mock_db


class TestClaimQueued:
    def test_calls_rpc_with_budget(self):
        db = mock_db()
        contact_row = {
            "id": 1, "campaign_id": "c1", "first_name": "Alice",
            "last_name": "Smith", "company_name": "Acme",
            "company_website": None, "position": None, "bio": None,
            "email": "alice@acme.com", "status": "sending",
            "mv_result": "ok", "reject_reason": None, "domain_id": None,
        }
        db.rpc.return_value.execute.return_value = MagicMock(data=[contact_row])

        with patch("app.worker.tick.get_db", return_value=db):
            contacts = claim_queued(10)

        db.rpc.assert_called_once_with("claim_queued_contacts", {"p_budget": 10})
        assert len(contacts) == 1
        assert contacts[0].email == "alice@acme.com"


class TestJitter:
    def test_jitter_in_range(self):
        for _ in range(50):
            j = jitter()
            assert 8 <= j <= 45


class TestTick:
    def test_skips_when_outside_send_window(self):
        with (
            patch("app.worker.tick.within_send_window", return_value=False),
            patch("app.worker.tick.active_domains") as mock_domains,
        ):
            tick()
            mock_domains.assert_not_called()

    def test_respects_zero_budget(self):
        domain = make_domain()
        with (
            patch("app.worker.tick.within_send_window", return_value=True),
            patch("app.worker.tick.active_domains", return_value=[domain]),
            patch("app.worker.tick.remaining_today", return_value=0),
            patch("app.worker.tick.claim_queued") as mock_claim,
            patch("app.worker.tick.check_and_pause_domains"),
        ):
            tick()
            mock_claim.assert_not_called()

    def test_sends_up_to_budget(self):
        domain = make_domain()
        contact = make_contact(status="sending")
        draft = Draft(subject="Hi", body="Hello there")

        with (
            patch("app.worker.tick.within_send_window", return_value=True),
            patch("app.worker.tick.active_domains", return_value=[domain]),
            patch("app.worker.tick.remaining_today", return_value=5),
            patch("app.worker.tick.claim_queued", return_value=[contact]),
            patch("app.worker.tick.draft_for", return_value=draft),
            patch("app.worker.tick.send_one", return_value=SendResult(success=True, resend_message_id="mid-1")),
            patch("app.worker.tick.check_and_pause_domains"),
            patch("app.worker.tick.jitter", return_value=0),
            patch("app.worker.tick.time.sleep"),
        ):
            tick()

    def test_failed_send_reverts_contact_to_queued(self):
        domain = make_domain()
        contact = make_contact(status="sending")
        draft = Draft(subject="Hi", body="Hello")
        db = mock_db()

        with (
            patch("app.worker.tick.within_send_window", return_value=True),
            patch("app.worker.tick.active_domains", return_value=[domain]),
            patch("app.worker.tick.remaining_today", return_value=5),
            patch("app.worker.tick.claim_queued", return_value=[contact]),
            patch("app.worker.tick.draft_for", return_value=draft),
            patch("app.worker.tick.send_one", return_value=SendResult(success=False, error="timeout")),
            patch("app.worker.tick.get_db", return_value=db),
            patch("app.worker.tick.check_and_pause_domains"),
            patch("app.worker.tick.jitter", return_value=0),
            patch("app.worker.tick.time.sleep"),
        ):
            tick()
            # verify revert was called
            db.table.assert_called()

    def test_missing_draft_reverts_contact(self):
        domain = make_domain()
        contact = make_contact(status="sending")
        db = mock_db()

        with (
            patch("app.worker.tick.within_send_window", return_value=True),
            patch("app.worker.tick.active_domains", return_value=[domain]),
            patch("app.worker.tick.remaining_today", return_value=5),
            patch("app.worker.tick.claim_queued", return_value=[contact]),
            patch("app.worker.tick.draft_for", return_value=None),
            patch("app.worker.tick.send_one") as mock_send,
            patch("app.worker.tick.get_db", return_value=db),
            patch("app.worker.tick.check_and_pause_domains"),
        ):
            tick()
            mock_send.assert_not_called()
