from unittest.mock import MagicMock, patch

from app.core.suppress import is_suppressed, suppress

from .conftest import mock_db


class TestIsSuppressed:
    def test_true_when_row_found(self):
        db = mock_db()
        db.execute.return_value = MagicMock(data=[{"id": 1}])
        with patch("app.core.suppress.get_db", return_value=db):
            assert is_suppressed("Alice@Acme.com") is True
        db.eq.assert_called_once_with("email", "alice@acme.com")

    def test_false_when_no_row(self):
        db = mock_db()
        db.execute.return_value = MagicMock(data=[])
        with patch("app.core.suppress.get_db", return_value=db):
            assert is_suppressed("alice@acme.com") is False


class TestSuppress:
    def test_writes_local_table_and_calls_resend(self):
        db = mock_db()
        with (
            patch("app.core.suppress.get_db", return_value=db),
            patch("app.core.suppress.resend.Suppressions.add") as mock_add,
        ):
            suppress("Alice@Acme.com", "unsubscribe")

        db.upsert.assert_called_once_with(
            {"email": "alice@acme.com", "reason": "unsubscribe"}, on_conflict="email"
        )
        mock_add.assert_called_once_with({"email": "alice@acme.com"})

    def test_local_write_survives_resend_failure(self):
        db = mock_db()
        with (
            patch("app.core.suppress.get_db", return_value=db),
            patch("app.core.suppress.resend.Suppressions.add", side_effect=Exception("boom")),
        ):
            suppress("alice@acme.com", "bounce")

        db.upsert.assert_called_once()
