-- Sender's own company name, used to prefix generated email subjects
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS sender_company_name text;
