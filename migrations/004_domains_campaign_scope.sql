-- Scope sending domains to campaigns
ALTER TABLE sending_domains ADD COLUMN IF NOT EXISTS campaign_id uuid REFERENCES campaigns(id) ON DELETE CASCADE;

-- Update claim_queued_contacts to support optional campaign filter
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
        SELECT id
        FROM contacts
        WHERE status = 'queued'
          AND (p_campaign_id IS NULL OR campaign_id = p_campaign_id)
        LIMIT p_budget
        FOR UPDATE SKIP LOCKED
    )
    RETURNING *;
END;
$$;
