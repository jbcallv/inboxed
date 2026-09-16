from unittest.mock import MagicMock, patch

from app.api.campaigns import PromptUpdate, get_generation_prompt, set_generation_prompt
from app.config import settings
from app.core import generate
from app.prompts import DEFAULT_GENERATION_PROMPT

from .conftest import make_contact, mock_db

USER = {"sub": "user-uuid"}


def _fake_message(text: str) -> MagicMock:
    message = MagicMock()
    message.content = [MagicMock(text=text)]
    return message


class TestGenerateEmailPrompt:
    def test_uses_custom_system_prompt(self):
        client = MagicMock()
        client.messages.create.return_value = _fake_message('{"subject": "Hi", "body": "Note"}')
        with patch("app.core.generate._get_client", return_value=client):
            generate.generate_email(make_contact(), "", "", "custom campaign prompt")
        sent = client.messages.create.call_args.kwargs["system"][0]["text"]
        assert sent == "custom campaign prompt"

    def test_falls_back_to_default_when_prompt_blank(self):
        client = MagicMock()
        client.messages.create.return_value = _fake_message('{"subject": "Hi", "body": "Note"}')
        with patch("app.core.generate._get_client", return_value=client):
            generate.generate_email(make_contact(), "", "", "")
        sent = client.messages.create.call_args.kwargs["system"][0]["text"]
        assert sent == settings.generation_system_prompt


class TestFormatSubject:
    def test_prefixes_with_both_company_names(self):
        assert generate.format_subject("Inboxed", "Acme Corp", "Cut reporting time in half") == (
            "Inboxed/Acme Corp - Cut reporting time in half"
        )

    def test_strips_whitespace(self):
        assert generate.format_subject("  Inboxed  ", "  Acme  ", "  blurb  ") == "Inboxed/Acme - blurb"

    def test_falls_back_when_names_blank(self):
        assert generate.format_subject("", "", "blurb") == "Us/You - blurb"


class TestBuildFullPrompt:
    def test_contains_system_prompt_and_contact_fields(self):
        contact = make_contact(first_name="Dana", last_name="Lee", bio="Runs a 5-person data team")
        full = generate.build_full_prompt(contact, "SYSTEM RULES HERE")
        assert "SYSTEM RULES HERE" in full
        assert "Dana Lee" in full
        assert "Runs a 5-person data team" in full


class TestGetGenerationPrompt:
    def test_returns_default_when_column_null(self):
        with (
            patch("app.api.campaigns.get_db", return_value=mock_db()),
            patch("app.api.campaigns._assert_owns"),
            patch("app.api.campaigns._stored_prompt", return_value=""),
            patch("app.api.campaigns._sample_contact", return_value=make_contact()),
        ):
            result = get_generation_prompt("campaign-uuid", USER)
        assert result["prompt"] == DEFAULT_GENERATION_PROMPT
        assert result["is_custom"] is False

    def test_returns_custom_when_set(self):
        with (
            patch("app.api.campaigns.get_db", return_value=mock_db()),
            patch("app.api.campaigns._assert_owns"),
            patch("app.api.campaigns._stored_prompt", return_value="my prompt"),
            patch("app.api.campaigns._sample_contact", return_value=make_contact()),
        ):
            result = get_generation_prompt("campaign-uuid", USER)
        assert result["prompt"] == "my prompt"
        assert result["is_custom"] is True


class TestSetGenerationPrompt:
    def test_writes_prompt(self):
        db = mock_db()
        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns._assert_owns"),
        ):
            set_generation_prompt("campaign-uuid", PromptUpdate(prompt="  keep this  "), USER)
        db.update.assert_called_once_with({"generation_prompt": "keep this"})

    def test_empty_prompt_clears_column(self):
        db = mock_db()
        with (
            patch("app.api.campaigns.get_db", return_value=db),
            patch("app.api.campaigns._assert_owns"),
        ):
            set_generation_prompt("campaign-uuid", PromptUpdate(prompt="   "), USER)
        db.update.assert_called_once_with({"generation_prompt": None})
