-- Resets contacts uploaded on 2026-09-18 back to unverified so /verify picks them up again.
-- Skips contacts already past the prep pipeline (drafted or later) so in-flight/sent emails aren't touched.
UPDATE contacts
SET status = 'new',
    mv_result = NULL,
    reject_reason = NULL
WHERE created_at::date = '2026-09-18'
  AND status NOT IN ('drafted', 'queued', 'sending', 'sent', 'bounced', 'complained', 'replied', 'hot_lead', 'unsubscribed');
