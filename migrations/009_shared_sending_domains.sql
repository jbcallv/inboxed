-- a sending domain can be reused across campaigns; its daily cap is shared by every campaign using it
ALTER TABLE sending_domains DROP CONSTRAINT sending_domains_domain_key;
ALTER TABLE sending_domains ADD CONSTRAINT sending_domains_campaign_domain_key UNIQUE (campaign_id, domain);
CREATE INDEX IF NOT EXISTS sending_domains_domain_idx ON sending_domains (domain);

CREATE OR REPLACE FUNCTION domain_sent_today(p_domain text)
RETURNS integer
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
    SELECT COALESCE(SUM(stats.sent_count), 0)::integer
    FROM domain_daily_stats stats
    JOIN sending_domains domains ON domains.id = stats.domain_id
    WHERE domains.domain = p_domain
      AND stats.date = CURRENT_DATE;
$$;
