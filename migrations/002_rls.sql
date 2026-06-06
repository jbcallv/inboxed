-- Enable RLS on all tenant tables
ALTER TABLE campaigns          ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts           ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_enrichments ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_emails    ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses          ENABLE ROW LEVEL SECURITY;

-- sending_domains and domain_daily_stats are shared across users (no per-user RLS)
-- suppressions are shared (global suppression list)

-- ─── campaigns ───────────────────────────────────────────────────────────────
CREATE POLICY campaigns_owner ON campaigns
    USING (user_id = auth.uid());

CREATE POLICY campaigns_owner_insert ON campaigns
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- ─── contacts (via campaign ownership) ───────────────────────────────────────
CREATE POLICY contacts_owner ON contacts
    USING (
        campaign_id IN (
            SELECT id FROM campaigns WHERE user_id = auth.uid()
        )
    );

-- ─── contact_enrichments ─────────────────────────────────────────────────────
CREATE POLICY enrichments_owner ON contact_enrichments
    USING (
        contact_id IN (
            SELECT c.id FROM contacts c
            JOIN campaigns ca ON ca.id = c.campaign_id
            WHERE ca.user_id = auth.uid()
        )
    );

-- ─── outreach_emails ─────────────────────────────────────────────────────────
CREATE POLICY outreach_owner ON outreach_emails
    USING (
        contact_id IN (
            SELECT c.id FROM contacts c
            JOIN campaigns ca ON ca.id = c.campaign_id
            WHERE ca.user_id = auth.uid()
        )
    );

-- ─── responses ───────────────────────────────────────────────────────────────
CREATE POLICY responses_owner ON responses
    USING (
        contact_id IN (
            SELECT c.id FROM contacts c
            JOIN campaigns ca ON ca.id = c.campaign_id
            WHERE ca.user_id = auth.uid()
        )
    );
