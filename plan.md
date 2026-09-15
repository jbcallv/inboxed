# Plan — CAN-SPAM compliance: physical address + unsubscribe

## Steps
1. Migration `006_unsubscribe_compliance.sql`: add `campaigns.physical_address text`;
   update `claim_queued_contacts` to exclude suppressed emails.
2. Bump `resend` dependency to a version with `Suppressions` support (`uv add`).
3. `backend/app/config.py`: add `frontend_url` setting.
4. `backend/app/utils/unsubscribe.py`: build unsubscribe URL + footer text (address + link).
5. `backend/app/api/campaigns.py`: attach footer to generated draft body in `_generate_contact`;
   add `PUT /campaigns/{id}/settings` to save `physical_address`; surface a warning during
   generation if no address is set yet.
6. `backend/app/core/suppress.py`: call `resend.Suppressions.add` alongside local table write.
7. `backend/app/api/unsubscribe.py` (new, no-auth router): `POST /api/unsubscribe` —
   validates contact belongs to campaign, suppresses email, marks contact `unsubscribed`.
8. Register new router in `main.py`.
9. Frontend: `/unsubscribe` public route (email + campaign query params, confirm button,
   success/error state).
10. Frontend: campaign settings section (physical address form) — new
    `/campaigns/[id]/settings` route + link tile from campaign detail page.
11. Tests: pytest for unsubscribe endpoint, suppress.py Resend call, claim_queued_contacts
    filter (SQL — document, can't unit test SQL directly, note in review), footer builder;
    vitest for the unsubscribe page.
12. Run full backend + frontend test suites; update `tasks/todo.md` with a completed section.

## Notes
- `backend/tests/test_prep_pipeline.py` currently fails to import (`_process_contact` doesn't
  exist — stale from an earlier refactor). Pre-existing, unrelated to this change; leaving as-is
  unless asked to fix.
