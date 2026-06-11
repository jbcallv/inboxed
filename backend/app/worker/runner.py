import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from ..config import settings
from .tick import tick
from .warmup import reset_daily_counts
from ..core.replies import fetch_and_record_replies

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    scheduler = BlockingScheduler(timezone=settings.send_timezone)

    scheduler.add_job(
        tick,
        IntervalTrigger(minutes=15),
        id="tick",
        name="send worker tick",
        max_instances=1,
        next_run_time=datetime.now(ZoneInfo(settings.send_timezone)),
    )
    scheduler.add_job(
        fetch_and_record_replies,
        IntervalTrigger(minutes=10),
        id="replies",
        name="Zoho IMAP reply poller",
        max_instances=1,
        next_run_time=datetime.now(ZoneInfo(settings.send_timezone)),
    )
    scheduler.add_job(
        reset_daily_counts,
        CronTrigger(hour=0, minute=0, timezone=settings.send_timezone),
        id="daily_reset",
        name="daily warmup reset",
        max_instances=1,
    )

    log.info("Worker started. Tick=15 min, Replies=10 min, Reset=midnight %s", settings.send_timezone)
    scheduler.start()


if __name__ == "__main__":
    main()
