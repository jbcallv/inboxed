import pytest
from app.utils.email_format import (
    is_valid_syntax,
    is_role_address,
    is_disposable,
    is_acceptable_format,
    normalize,
    dedupe,
)


class TestSyntax:
    def test_valid_email(self):
        assert is_valid_syntax("alice@example.com")

    def test_invalid_no_at(self):
        assert not is_valid_syntax("notanemail")

    def test_invalid_no_domain(self):
        assert not is_valid_syntax("alice@")

    def test_invalid_no_tld(self):
        assert not is_valid_syntax("alice@example")

    def test_valid_subdomain(self):
        assert is_valid_syntax("alice@mail.example.co.uk")

    def test_valid_plus_address(self):
        assert is_valid_syntax("alice+tag@example.com")


class TestRoleAddress:
    def test_info_is_role(self):
        assert is_role_address("info@acme.com")

    def test_sales_is_role(self):
        assert is_role_address("sales@acme.com")

    def test_noreply_is_role(self):
        assert is_role_address("noreply@acme.com")

    def test_normal_is_not_role(self):
        assert not is_role_address("alice@acme.com")

    def test_case_insensitive(self):
        assert is_role_address("INFO@acme.com")


class TestDisposable:
    def test_mailinator_is_disposable(self):
        assert is_disposable("test@mailinator.com")

    def test_yopmail_is_disposable(self):
        assert is_disposable("test@yopmail.com")

    def test_real_domain_is_not_disposable(self):
        assert not is_disposable("alice@gmail.com")


class TestIsAcceptableFormat:
    def test_valid_passes(self):
        ok, reason = is_acceptable_format("alice@example.com")
        assert ok
        assert reason == ""

    def test_role_rejected(self):
        ok, reason = is_acceptable_format("info@example.com")
        assert not ok
        assert reason == "role_address"

    def test_disposable_rejected(self):
        ok, reason = is_acceptable_format("x@mailinator.com")
        assert not ok
        assert reason == "disposable_domain"

    def test_bad_syntax_rejected(self):
        ok, reason = is_acceptable_format("notvalid")
        assert not ok
        assert reason == "invalid_syntax"

    def test_strips_and_lowercases(self):
        ok, reason = is_acceptable_format("  Alice@Example.COM  ")
        assert ok


class TestNormalize:
    def test_lowercases(self):
        assert normalize("Alice@Example.COM") == "alice@example.com"

    def test_strips(self):
        assert normalize("  alice@example.com  ") == "alice@example.com"


class TestDedupe:
    def test_removes_duplicates(self):
        result = dedupe(["alice@example.com", "ALICE@EXAMPLE.COM", "bob@example.com"])
        assert len(result) == 2

    def test_preserves_order(self):
        emails = ["c@example.com", "a@example.com", "b@example.com"]
        assert dedupe(emails) == emails
