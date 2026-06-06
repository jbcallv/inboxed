-- Claim queued contacts atomically using FOR UPDATE SKIP LOCKED.
-- Updates status to 'sending' and returns the claimed rows.
-- Called by the send worker; runs as service role (bypasses RLS).
CREATE OR REPLACE FUNCTION claim_queued_contacts(p_budget integer)
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
        LIMIT p_budget
        FOR UPDATE SKIP LOCKED
    )
    RETURNING *;
END;
$$;

-- Upsert today's domain stats row and increment a counter.
CREATE OR REPLACE FUNCTION increment_domain_stat(
    p_domain_id uuid,
    p_column    text,
    p_amount    integer DEFAULT 1
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    INSERT INTO domain_daily_stats (domain_id, date)
    VALUES (p_domain_id, CURRENT_DATE)
    ON CONFLICT (domain_id, date) DO NOTHING;

    EXECUTE format(
        'UPDATE domain_daily_stats SET %I = %I + $1 WHERE domain_id = $2 AND date = CURRENT_DATE',
        p_column, p_column
    ) USING p_amount, p_domain_id;
END;
$$;
