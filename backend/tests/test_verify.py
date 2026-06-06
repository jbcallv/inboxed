import pytest
from unittest.mock import MagicMock, patch
from app.core.verify import verify_email, is_deliverable, verify_contact
from app.core.models import VerifyResult
from .conftest import make_contact, mock_db


class TestIsDeliverable:
    def test_ok_is_deliverable(self):
        assert is_deliverable(VerifyResult(email="a@b.com", code="ok"))

    def test_catch_all_is_not(self):
        assert not is_deliverable(VerifyResult(email="a@b.com", code="catch_all"))

    def test_invalid_is_not(self):
        assert not is_deliverable(VerifyResult(email="a@b.com", code="invalid"))

    def test_unknown_is_not(self):
        assert not is_deliverable(VerifyResult(email="a@b.com", code="unknown"))


class TestVerifyEmail:
    def test_calls_mv_api_and_returns_result(self):
        with patch("app.core.verify.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"result": "ok", "email": "alice@acme.com"},
            )
            mock_get.return_value.raise_for_status = lambda: None
            result = verify_email("alice@acme.com")
            assert result.code == "ok"
            assert result.email == "alice@acme.com"

    def test_returns_unknown_on_missing_result_field(self):
        with patch("app.core.verify.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {},
            )
            mock_get.return_value.raise_for_status = lambda: None
            result = verify_email("alice@acme.com")
            assert result.code == "unknown"


class TestVerifyContact:
    def test_ok_contact_advances_to_verified(self):
        contact = make_contact(email="alice@acme.com", status="verifying")
        db = mock_db()

        with (
            patch("app.core.verify.get_db", return_value=db),
            patch("app.core.verify.suppress_module.is_suppressed", return_value=False),
            patch("app.core.verify.verify_email", return_value=VerifyResult(email="alice@acme.com", code="ok")),
        ):
            result = verify_contact(contact)
            assert result.status == "verified"
            assert result.mv_result == "ok"

    def test_invalid_mv_result_rejects_contact(self):
        contact = make_contact(email="alice@acme.com", status="verifying")
        db = mock_db()

        with (
            patch("app.core.verify.get_db", return_value=db),
            patch("app.core.verify.suppress_module.is_suppressed", return_value=False),
            patch("app.core.verify.verify_email", return_value=VerifyResult(email="alice@acme.com", code="invalid")),
        ):
            result = verify_contact(contact)
            assert result.status == "rejected"
            assert result.reject_reason == "invalid"

    def test_role_address_rejected_before_mv_call(self):
        contact = make_contact(email="info@acme.com", status="verifying")
        db = mock_db()

        with (
            patch("app.core.verify.get_db", return_value=db),
            patch("app.core.verify.verify_email") as mock_mv,
        ):
            result = verify_contact(contact)
            assert result.status == "rejected"
            assert result.reject_reason == "role_address"
            mock_mv.assert_not_called()

    def test_suppressed_email_rejected_before_mv_call(self):
        contact = make_contact(email="alice@acme.com", status="verifying")
        db = mock_db()

        with (
            patch("app.core.verify.get_db", return_value=db),
            patch("app.core.verify.suppress_module.is_suppressed", return_value=True),
            patch("app.core.verify.verify_email") as mock_mv,
        ):
            result = verify_contact(contact)
            assert result.status == "rejected"
            assert result.reject_reason == "suppressed"
            mock_mv.assert_not_called()

    def test_catch_all_rejected(self):
        contact = make_contact(email="alice@acme.com", status="verifying")
        db = mock_db()

        with (
            patch("app.core.verify.get_db", return_value=db),
            patch("app.core.verify.suppress_module.is_suppressed", return_value=False),
            patch("app.core.verify.verify_email", return_value=VerifyResult(email="alice@acme.com", code="catch_all")),
        ):
            result = verify_contact(contact)
            assert result.status == "rejected"
            assert result.mv_result == "catch_all"
