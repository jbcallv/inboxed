-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── campaigns ───────────────────────────────────────────────────────────────
CREATE TABLE campaigns (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL,
    name            text NOT NULL,
    status          text NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft','prepping','ready','sending','done','paused')),
    sample_approved boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- ─── contacts ────────────────────────────────────────────────────────────────
CREATE TABLE contacts (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_id     uuid NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    first_name      text,
    last_name       text,
    company_name    text,
    company_website text,
    position        text,
    bio             text,
    email           text,
    status          text NOT NULL DEFAULT 'new'
                        CHECK (status IN (
                            'new','finding','no_email','verifying','rejected',
                            'verified','enriching','enriched','generating',
                            'drafted','queued','sending','sent',
                            'bounced','complained','replied','hot_lead','unsubscribed'
                        )),
    mv_result       text,
    reject_reason   text,
    domain_id       uuid,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX contacts_campaign_status ON contacts(campaign_id, status);
CREATE INDEX contacts_status ON contacts(status);

-- ─── contact_enrichments ─────────────────────────────────────────────────────
CREATE TABLE contact_enrichments (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    contact_id      bigint NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    website_content text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (contact_id)
);

-- ─── outreach_emails ─────────────────────────────────────────────────────────
CREATE TABLE outreach_emails (
    id                  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    contact_id          bigint NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    subject             text NOT NULL,
    body                text NOT NULL,
    status              text NOT NULL DEFAULT 'draft'
                            CHECK (status IN ('draft','sent','bounced','replied')),
    resend_message_id   text,
    sent_at             timestamptz,
    created_at          timestamptz NOT NULL DEFAULT now()
);

-- ─── sending_domains ─────────────────────────────────────────────────────────
CREATE TABLE sending_domains (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    domain              text NOT NULL UNIQUE,
    from_name           text NOT NULL,
    from_locals         text[] NOT NULL DEFAULT '{}',
    status              text NOT NULL DEFAULT 'warming'
                            CHECK (status IN ('warming','active','paused')),
    warmup_started_on   date NOT NULL DEFAULT CURRENT_DATE,
    steady_cap_override int,
    created_at          timestamptz NOT NULL DEFAULT now()
);

-- ─── domain_daily_stats ──────────────────────────────────────────────────────
CREATE TABLE domain_daily_stats (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    domain_id       uuid NOT NULL REFERENCES sending_domains(id) ON DELETE CASCADE,
    date            date NOT NULL DEFAULT CURRENT_DATE,
    sent_count      int NOT NULL DEFAULT 0,
    bounce_count    int NOT NULL DEFAULT 0,
    complaint_count int NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (domain_id, date)
);

-- ─── responses ───────────────────────────────────────────────────────────────
CREATE TABLE responses (
    id                  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    contact_id          bigint NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    outreach_email_id   bigint REFERENCES outreach_emails(id),
    imap_uid            text NOT NULL,
    reply_body          text,
    sentiment           text CHECK (sentiment IN ('positive','neutral','negative','unsubscribe')),
    is_hot_lead         boolean NOT NULL DEFAULT false,
    received_at         timestamptz,
    created_at          timestamptz NOT NULL DEFAULT now()
);

-- ─── suppressions ────────────────────────────────────────────────────────────
CREATE TABLE suppressions (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email       text NOT NULL UNIQUE,
    reason      text NOT NULL CHECK (reason IN ('bounce','complaint','unsubscribe')),
    created_at  timestamptz NOT NULL DEFAULT now()
);
