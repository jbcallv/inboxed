-- campaigns.status was missing 'verified', the state set between verify and generate steps
ALTER TABLE campaigns DROP CONSTRAINT campaigns_status_check;
ALTER TABLE campaigns ADD CONSTRAINT campaigns_status_check
    CHECK (status IN ('draft','prepping','verified','ready','sending','done','paused'));
