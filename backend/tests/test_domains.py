import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from app.core.domains import cap_today, remaining_today, pick_domain, check_and_pause_domains
from app.core.models import SendingDomain
from .conftest import make_domain, mock_db


class TestCapToday:
    def test_day_zero_returns_start_cap(self):
        domain = make_domain(warmup_started_on=date.today())
        # day=0: cap = min(250, 20 + 25*0) = 20
        assert cap_today(domain) == 20

    def test_day_ten_caps_at_steady(self):
        from datetime import timedelta
        started = date.today() - timedelta(days=100)
        domain = make_domain(warmup_started_on=started)
        assert cap_today(domain) == 250

    def test_day_five_intermediate(self):
        from datetime import timedelta
        started = date.today() - timedelta(days=5)
        domain = make_domain(warmup_started_on=started)
        # cap = min(250, 20 + 25*5) = min(250, 145) = 145
        assert cap_today(domain) == 145

    def test_steady_cap_override(self):
        domain = make_domain(warmup_started_on=date.today(), steady_cap_override=100)
        # cap = min(100, 20 + 0) = 20 (still ramping)
        assert cap_today(domain) == 20

    def test_override_applies_at_steady(self):
        from datetime import timedelta
        started = date.today() - timedelta(days=100)
        domain = make_domain(warmup_started_on=started, steady_cap_override=100)
        assert cap_today(domain) == 100


class TestRemainingToday:
    def test_returns_cap_minus_sent(self):
        domain = make_domain(warmup_started_on=date.today())  # cap = 20
        db = mock_db()
        db.execute.return_value = MagicMock(data=[{"sent_count": 5}])

        with patch("app.core.domains.get_db", return_value=db):
            remaining = remaining_today(domain)
        assert remaining == 15

    def test_no_stats_row_means_zero_sent(self):
        domain = make_domain(warmup_started_on=date.today())  # cap = 20
        db = mock_db()
        db.execute.return_value = MagicMock(data=[])

        with patch("app.core.domains.get_db", return_value=db):
            remaining = remaining_today(domain)
        assert remaining == 20

    def test_cannot_go_below_zero(self):
        domain = make_domain(warmup_started_on=date.today())  # cap = 20
        db = mock_db()
        db.execute.return_value = MagicMock(data=[{"sent_count": 999}])

        with patch("app.core.domains.get_db", return_value=db):
            remaining = remaining_today(domain)
        assert remaining == 0


class TestPickDomain:
    def test_picks_domain_with_most_remaining(self):
        from datetime import timedelta
        # domain1 has 0 remaining (day0, already sent 20)
        # domain2 has 10 remaining
        domain1 = make_domain(id="d1", warmup_started_on=date.today())
        domain2 = make_domain(id="d2", warmup_started_on=date.today())

        def fake_remaining(d):
            return 0 if d.id == "d1" else 10

        with patch("app.core.domains.remaining_today", side_effect=fake_remaining):
            result = pick_domain([domain1, domain2])
        assert result.id == "d2"

    def test_returns_none_when_all_exhausted(self):
        domain = make_domain(warmup_started_on=date.today())
        with patch("app.core.domains.remaining_today", return_value=0):
            result = pick_domain([domain])
        assert result is None

    def test_returns_none_for_empty_list(self):
        assert pick_domain([]) is None


class TestAutoAutoPause:
    def test_high_bounce_rate_pauses_domain(self):
        db = mock_db()
        # 3 domains in 'active' status, 1 with high bounce rate
        db.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{"id": "d1", "domain": "test.com", "status": "active"}]
        )
        # Mock stats: 100 sent, 5 bounced (5% > 3% threshold)
        stats_result = MagicMock(data=[
            {"sent_count": 100, "bounce_count": 5, "complaint_count": 0},
        ])

        def table_side(name):
            mock = MagicMock()
            mock.select.return_value = mock
            mock.eq.return_value = mock
            mock.in_.return_value = mock
            mock.order.return_value = mock
            mock.limit.return_value = mock
            mock.update.return_value = mock
            if name == "domain_daily_stats":
                mock.execute.return_value = stats_result
            else:
                mock.execute.return_value = MagicMock(
                    data=[{"id": "d1", "domain": "test.com", "status": "active"}]
                )
            return mock

        db.table.side_effect = table_side
        with patch("app.core.domains.get_db", return_value=db):
            check_and_pause_domains()
