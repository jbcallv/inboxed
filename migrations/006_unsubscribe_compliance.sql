-- CAN-SPAM compliance: per-campaign postal address, and enforce suppressions at claim time
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS physical_address text;

-- Exclude suppressed emails so unsubscribed/bounced/complained contacts are never claimed to send
CREATE OR REPLACE FUNCTION claim_queued_contacts(p_budget integer, p_campaign_id uuid DEFAULT NULL)
RETURNS SETOF contacts
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    UPDATE contacts
    SET status = 'sending'
    WHERE id IN (
        SELECT c.id
        FROM contacts c
        WHERE c.status = 'queued'
          AND (p_campaign_id IS NULL OR c.campaign_id = p_campaign_id)
          AND NOT EXISTS (
              SELECT 1 FROM suppressions s WHERE s.email = lower(trim(c.email))
          )
        LIMIT p_budget
        FOR UPDATE SKIP LOCKED
    )
    RETURNING *;
END;
$$;
