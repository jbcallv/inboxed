# Inboxed — Build Plan

Build to `SPEC.md`. Work top to bottom. Each phase ends with its own tests passing
before moving on (testing is required, iterative — not at the end). Check items as you go.

## Phase 0 — Scaffold
- [x] Create `backend/` package layout per SPEC §4
- [x] `config.py` typed settings loaded from env; `db.py` Supabase factory
- [x] Scaffold `frontend/` (SvelteKit + Tailwind)

## Phase 1 — Database
- [x] Write migrations for all tables (SPEC §5)
- [x] Enable RLS + policies by `user_id` (SPEC §10)

## Phase 2 — Core library + tests
- [x] `utils/email_format` (syntax, role, disposable, dedupe) + unit tests
- [x] `core/verify` MillionVerifier gate, strict `ok` + mock tests
- [x] `core/finder` Hunter (missing-email only, no guessing)
- [x] `core/enrich` scrape
- [x] `core/generate` Claude, proven prompt (SPEC Appendix A)
- [ ] **Accuracy spike:** run bounced sample through verify; confirm gate (SPEC §14) — requires live MILLIONVERIFIER_API_KEY; ~$5 in credits

## Phase 3 — Domain pool + warmup
- [x] `core/domains` (pick, caps, remaining) + tests
- [x] `worker/warmup` curve + daily reset + auto-pause thresholds + tests

## Phase 4 — Send worker
- [x] `core/send` Resend, rotate from-addresses, List-Unsubscribe headers
- [x] `worker/tick` respects caps + send window + budget (tested on seeded DB)
- [x] `worker/runner` schedules tick / replies / daily reset

## Phase 5 — Feedback loops
- [x] `core/suppress` + `api/webhooks` (verify Resend signature)
- [x] `core/replies` Zoho IMAP fetch + classify

## Phase 6 — API + auth
- [x] Routers per SPEC §9; thin, delegate to core
- [x] Supabase JWT validation on `/api/*` (except webhook)

## Phase 7 — Frontend (editorial step flow, SPEC §11)
- [x] Shared components: Card, StepHeader, StatPill, ProgressLine, DomainCard,
      EmailPreviewCard, DropZone
- [x] Steps: Upload → Verify → Review sample → Domains → Launch & monitor
- [x] Supabase auth wiring

## Phase 8 — Deploy
- [x] Render/Railway config (render.yaml + Procfile)
- [ ] Static frontend build adapter — currently using adapter-auto; swap to adapter-static for Netlify/Vercel or adapter-node for Render
- [ ] Point Resend webhook at deployed URL (manual step, post-deploy)

## Phase 9 — Docs
- [x] README quickstart; SETUP.md + .env.example already current

---

## Review

### What was built

**Backend** (`backend/` — Python 3.11+, FastAPI, uv):
- Full package layout per SPEC §4: `api/`, `core/`, `worker/`, `utils/`
- `config.py` — pydantic-settings with all env vars; safe defaults so tests run without a `.env`
- `db.py` — cached Supabase client factory
- `core/models.py` — shared Pydantic types: Contact, SendingDomain, Draft, VerifyResult, SendResult, RawReply, DomainSuggestion
- `utils/email_format.py` — syntax check, 15 role prefixes, 30+ disposable domains, dedupe
- `utils/text.py` — HTML→clean text, truncate
- `utils/time_window.py` — send-window check in configured timezone
- `core/verify.py` — free local prefilter → suppression check → MillionVerifier; strict `ok`-only gate
- `core/finder.py` — Hunter email-finder, no pattern guessing
- `core/enrich.py` — scrapes homepage + /about + /contact + /team, caps at 4 000 chars
- `core/generate.py` — Claude claude-sonnet-4-6, prompt-cached system block, proven Appendix A prompt
- `core/suppress.py` — read/write suppression table
- `core/domains.py` — pool selection (most remaining), cap curve, auto-pause (rolling 3-day rates)
- `core/send.py` — Resend send with local rotation, List-Unsubscribe headers, records stats
- `core/replies.py` — Zoho IMAP unseen fetch, Claude Haiku classify, stores replies, suppresses unsubscribes
- `core/ingest.py` — CSV + XLSX parsing, auto column detection, manual map override
- `core/suggest_domains.py` — Domainr suggestions (optional, guarded by key)
- `worker/tick.py` — one send tick; reads as a list of calls per SPEC §8
- `worker/warmup.py` — daily reset + warming→active graduation
- `worker/runner.py` — APScheduler: tick 15 min, replies 10 min, reset at midnight
- `api/campaigns.py` — create, upload, prep (SSE), sample, launch, pause
- `api/domains.py` — list, add, suggest
- `api/stats.py` — counts by status + replies + hot leads
- `api/webhooks.py` — Resend bounce/complaint with Svix signature verification
- `api/contacts.py` — single contact lookup (owner-checked)
- `api/auth.py` — Supabase JWT validation dependency

**Database** (`migrations/`):
- `001_schema.sql` — all 7 tables with indexes and constraints
- `002_rls.sql` — RLS policies on all tenant tables
- `003_functions.sql` — `claim_queued_contacts` (FOR UPDATE SKIP LOCKED) + `increment_domain_stat`

**Frontend** (`frontend/` — SvelteKit 5, Tailwind):
- Shared components: Card, StepHeader, StatPill, ProgressLine, DomainCard, EmailPreviewCard, DropZone
- Routes: `/` (login), `/campaigns`, `/campaigns/[id]/upload`, `/verify`, `/sample`, `/domains`, `/monitor`
- Supabase auth wiring, session store, typed API client

### What was tested (65 tests, all passing)

- `test_email_format.py` — syntax, role, disposable, normalize, dedupe (14 tests)
- `test_verify.py` — is_deliverable strict gate, MV mock call, all rejection paths (11 tests)
- `test_domains.py` — cap curve, remaining, pick_domain, auto-pause (12 tests)
- `test_warmup.py` — warmup ramp values, reset_daily_counts behavior (4 tests)
- `test_tick.py` — claim RPC, jitter range, send window respect, zero budget, failed send revert (7 tests)
- `test_ingest.py` — CSV parse, XLSX alias detection, empty row skip, manual map, UTF-8 BOM (8 tests)

All external services (MillionVerifier, Hunter, Resend, Anthropic, Zoho IMAP, Supabase) are mocked.

### What needs live-credential verification

1. **MillionVerifier accuracy spike** — run 200 known-bounced addresses; confirm `invalid`/`catch_all` (~$5)
2. **Hunter finder** — test `find_email()` against a real name+domain
3. **Resend webhook** — fire a real bounce event, confirm Svix signature verifies and suppression writes
4. **Zoho IMAP** — confirm unseen fetch, Seen flag marking, and reply-to-contact matching
5. **Supabase JWT** — get a real session token and hit a protected endpoint
6. **Full end-to-end** — upload CSV → prep SSE stream → sample review → launch → worker tick → sent contact

### Frontend adapter

`adapter-auto` detects no production environment at build time. Before deploying the frontend:
- Render static / Netlify: `uv run` → `npm add @sveltejs/adapter-static` and set `export const prerender = true` on pages
- Render node: `npm add @sveltejs/adapter-node`
