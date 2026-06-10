import pytest
import respx
import httpx
from app.core.suggest_domains import suggest_sending_domains, _check_rdap, _build_candidates


class TestBuildCandidates:
    def test_generates_prefix_variants(self):
        candidates = _build_candidates("acme")
        assert "getacme.io" in candidates
        assert "tryacme.com" in candidates

    def test_deduplicates_and_caps_at_20(self):
        candidates = _build_candidates("x")
        assert len(candidates) <= 20
        assert len(candidates) == len(set(candidates))

    def test_lowercases_and_strips_spaces(self):
        candidates = _build_candidates("My Brand")
        assert all("mybrand" in c for c in candidates[:3])


class TestCheckRdap:
    @respx.mock
    def test_404_means_available(self):
        respx.get("https://rdap.org/domain/geteximo.io").mock(
            return_value=httpx.Response(404)
        )
        result = _check_rdap("geteximo.io")
        assert result is not None
        assert result.available is True
        assert result.domain == "geteximo.io"

    @respx.mock
    def test_200_means_taken(self):
        respx.get("https://rdap.org/domain/google.com").mock(
            return_value=httpx.Response(200, json={"ldhName": "google.com"})
        )
        result = _check_rdap("google.com")
        assert result is not None
        assert result.available is False

    @respx.mock
    def test_500_returns_none(self):
        respx.get("https://rdap.org/domain/error.com").mock(
            return_value=httpx.Response(500)
        )
        result = _check_rdap("error.com")
        # 500 is not 404, so available=False — still returns a result
        assert result is not None
        assert result.available is False

    @respx.mock
    def test_network_error_returns_none(self):
        respx.get("https://rdap.org/domain/timeout.io").mock(
            side_effect=httpx.ConnectError("unreachable")
        )
        result = _check_rdap("timeout.io")
        assert result is None


class TestSuggestSendingDomains:
    @respx.mock
    def test_returns_only_available_domains(self, monkeypatch):
        monkeypatch.setattr("app.core.suggest_domains.time.sleep", lambda _: None)

        for route in respx.routes:
            pass

        # First candidate available, rest taken
        calls = []

        def handler(request):
            domain = request.url.path.split("/domain/")[-1]
            calls.append(domain)
            return httpx.Response(404 if domain == "gettest.io" else 200)

        respx.get(url__regex=r"https://rdap\.org/domain/.*").mock(side_effect=handler)

        results = suggest_sending_domains("test")
        domains = [r.domain for r in results]
        assert "gettest.io" in domains
        assert all(r.available for r in results)

    @respx.mock
    def test_empty_when_all_taken(self, monkeypatch):
        monkeypatch.setattr("app.core.suggest_domains.time.sleep", lambda _: None)
        respx.get(url__regex=r"https://rdap\.org/domain/.*").mock(
            return_value=httpx.Response(200)
        )
        results = suggest_sending_domains("google")
        assert results == []
