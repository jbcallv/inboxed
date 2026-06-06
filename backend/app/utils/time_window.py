from datetime import datetime
from zoneinfo import ZoneInfo
from ..config import settings


def now_in_send_tz() -> datetime:
    return datetime.now(ZoneInfo(settings.send_timezone))


def within_send_window() -> bool:
    now = now_in_send_tz()
    return settings.send_window_start <= now.hour < settings.send_window_end
