"""Dev helper: run a single tick immediately, bypassing the send window check."""
import logging
from .tick import claim_queued, draft_for, _mark_failed, check_and_pause_domains
from ..core.domains import active_domains, remaining_today
from ..core.send import send_one

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def run(count: int | None = None):
    from ..db import get_db
    db = get_db()
    campaigns = db.table("campaigns").select("id,name").eq("status", "sending").execute().data
    if not campaigns:
        log.warning("No campaigns in 'sending' status. Launch a campaign first.")
        return

    remaining = count
    for campaign in campaigns:
        if remaining is not None and remaining <= 0:
            break
        campaign_id = campaign["id"]
        log.info("Campaign: %s (%s)", campaign["name"], campaign_id)
        domains = active_domains(campaign_id)
        if not domains:
            log.warning("  No active domains for this campaign.")
            continue

        for domain in domains:
            if remaining is not None and remaining <= 0:
                break
            budget = remaining_today(domain)
            if count is not None:
                budget = min(budget, remaining)
            log.info("  Domain %s — budget: %d", domain.domain, budget)
            if budget <= 0:
                log.info("  Domain %s at daily cap, skipping.", domain.domain)
                continue

            contacts = claim_queued(budget, campaign_id)
            log.info("  Claimed %d contacts", len(contacts))
            for contact in contacts:
                draft = draft_for(contact)
                if draft is None:
                    log.warning("  No draft for contact %s — reverting to queued.", contact.id)
                    _mark_failed(contact)
                    continue

                result = send_one(domain, contact, draft)
                if result.success:
                    log.info("  Sent to %s (%s) — message id: %s", contact.email, contact.id, result.resend_message_id)
                    if remaining is not None:
                        remaining -= 1
                else:
                    log.warning("  Send failed for %s: %s", contact.email, result.error)
                    _mark_failed(contact)

    check_and_pause_domains()
    log.info("Tick complete.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run one send tick immediately, bypassing the send window.")
    parser.add_argument("--count", "-n", type=int, default=None, help="Max emails to send (default: all queued)")
    args = parser.parse_args()
    run(count=args.count)
