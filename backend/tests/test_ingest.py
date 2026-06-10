import csv
import io
import pytest
from app.core.ingest import parse_upload, _detect_mapping


class TestDetectMapping:
    def test_detects_email_column(self):
        mapping = _detect_mapping(["Email Address", "First Name", "Last Name"])
        assert "email" in mapping
        assert "first_name" in mapping

    def test_handles_canonical_names(self):
        mapping = _detect_mapping(["first_name", "last_name", "email"])
        assert mapping["first_name"] == "first_name"
        assert mapping["email"] == "email"

    def test_unknown_columns_ignored(self):
        mapping = _detect_mapping(["random_column", "another_random"])
        assert mapping == {}


class TestParseUploadCSV:
    def _make_csv(self, rows: list[dict], fieldnames: list[str]) -> bytes:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue().encode()

    def test_parses_basic_csv(self):
        content = self._make_csv(
            [{"email": "alice@acme.com", "first_name": "Alice", "last_name": "Smith"}],
            ["email", "first_name", "last_name"],
        )
        rows = parse_upload(content, "contacts.csv")
        assert len(rows) == 1
        assert rows[0]["email"] == "alice@acme.com"
        assert rows[0]["first_name"] == "Alice"

    def test_auto_detects_column_aliases(self):
        content = self._make_csv(
            [{"Email Address": "bob@acme.com", "First Name": "Bob"}],
            ["Email Address", "First Name"],
        )
        rows = parse_upload(content, "contacts.csv")
        assert len(rows) == 1
        assert rows[0]["email"] == "bob@acme.com"

    def test_skips_empty_rows(self):
        content = self._make_csv(
            [
                {"email": "alice@acme.com", "first_name": "Alice"},
                {"email": "", "first_name": ""},
            ],
            ["email", "first_name"],
        )
        rows = parse_upload(content, "contacts.csv")
        assert len(rows) == 1

    def test_manual_column_map_overrides_detection(self):
        content = self._make_csv(
            [{"addr": "carol@acme.com", "fn": "Carol"}],
            ["addr", "fn"],
        )
        rows = parse_upload(content, "contacts.csv", column_map={"email": "addr", "first_name": "fn"})
        assert rows[0]["email"] == "carol@acme.com"
        assert rows[0]["first_name"] == "Carol"

    def test_handles_utf8_bom(self):
        content = b"\xef\xbb\xbfemail,first_name\nalice@acme.com,Alice\n"
        rows = parse_upload(content, "contacts.csv")
        assert rows[0]["email"] == "alice@acme.com"

    def test_rejects_rows_with_no_email(self):
        content = self._make_csv(
            [
                {"first_name": "Alice", "last_name": "Smith", "email": "alice@acme.com"},
                {"first_name": "Bob",   "last_name": "Jones", "email": ""},
            ],
            ["first_name", "last_name", "email"],
        )
        rows = parse_upload(content, "contacts.csv")
        assert len(rows) == 1
        assert rows[0]["first_name"] == "Alice"

    def test_accepts_nameless_row_with_email(self):
        # Company-only contacts (no personal name) are valid if they have an email
        content = self._make_csv(
            [{"first_name": "", "last_name": "", "email": "info@acme.com", "company_name": "Acme Corp"}],
            ["first_name", "last_name", "email", "company_name"],
        )
        rows = parse_upload(content, "contacts.csv")
        assert len(rows) == 1
        assert rows[0]["email"] == "info@acme.com"

    def test_name_column_maps_to_company_name(self):
        content = self._make_csv(
            [{"first_name": "Alice", "email": "alice@acme.com", "name": "Acme Corp"}],
            ["first_name", "email", "name"],
        )
        rows = parse_upload(content, "contacts.csv")
        assert rows[0]["company_name"] == "Acme Corp"
