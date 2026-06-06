# Inboxed — Build Spec

Verified, personalized cold email that lands in the inbox — sent autonomously across a
warmed pool of sending domains, staying under deliverability limits without a human
watching.

This document is the source of truth. Build to this spec from scratch. When a decision
is ambiguous, prefer the simpler option and follow `claude.md`.

---

## 1. The core idea

Cold email fails for two reasons: bad addresses (bounces) and bad reputation (spam
folder). Inboxed fixes both structurally:

- **Verification is a hard gate, before any paid step.** No email-finder credit, no
  Claude token, and no send is ever spent on an address that is not confirmed
  deliverable. Keep only MillionVerifier `ok`. No pattern-guessing, ever.
- **Sending is spread across a warmed domain pool** with per-domain daily caps, send
  windows, and automatic pausing if bounce/complaint rates rise — so the sending
  account is never at risk.

The product wins on getting a great email into the inbox autonomously. Nothing else.

---

## 2. Principles (from claude.md)

- Simplicity first. Fewest features that make it effective.
- One responsibility per module, class, and function. `main` and `tick` read as a list
  of named function calls, not logic.
- Components small, single-purpose, reused. No CLI scripts — everything is importable
  library code called by the API or the worker.
- Token-minimal final code: short functions, intention-revealing names, no dead code.
- Light, minimal, editorial UI (see §11). Tailwind only.

---

## 3. Architecture at a glance

Two independent pipelines over one Supabase Postgres database:

1. **Prep pipeline** — fast, API-bound, runs right after a list is uploaded:
   `ingest → (find if missing) → verify → enrich → generate → queued`.
   Burns credits, but only on verified-deliverable contacts.

2. **Send worker** — slow, deliverability-bound, runs autonomously 24/7:
   pulls `queued` contacts and sends them across the warmed domain pool, respecting
   per-domain daily caps, the send window, and bounce/complaint safety limits.

Supporting loops on the same worker process:
- **Reply poller** — Zoho IMAP → classify → store.
- **Suppression** — Resend webhooks (bounce/complaint) → suppress + update domain stats.

**Supabase Postgres is the queue.** No Redis, Celery, or SQS. Concurrency uses
`SELECT … FOR UPDATE SKIP LOCKED`.

```
upload ──▶ ingest ──▶ find* ──▶ VERIFY ──▶ enrich ──▶ generate ──▶ queued
                                  │(strict gate: keep result=="ok")
                                  ▼
                               rejected (archived, never touched again)

queued ──▶ [send worker tick] ──▶ sent ──▶ (webhook) ──▶ bounced/complained
                                     │
                                     └──▶ (IMAP) ──▶ replied / hot_lead / unsubscribed
```
`*find` runs only for rows missing an email.

---

## 4. Repository layout

Fresh build — no legacy code. Target structure:

```
inboxed/
  claude.md            # rules (root, auto-loaded)
  SPEC.md
  SETUP.md
  .env.example
  tasks/
    todo.md
    lessons.md
  migrations/          # SQL migrations
  backend/
    pyproject.toml
    app/
      main.py          # builds FastAPI app, includes routers — nothing else
      config.py        # typed settings loaded from env (one place)
      db.py            # supabase client factory
      api/             # HTTP layer — thin, delegates to core
        campaigns.py
        contacts.py
        domains.py
        stats.py
        webhooks.py    # POST /api/webhooks/resend
      core/            # library — one file per responsibility
        ingest.py        # parse upload -> contact rows
        finder.py        # Hunter email-finder (only for missing emails)
        verify.py        # MillionVerifier gate
        enrich.py        # scrape company site -> text
        generate.py      # Claude -> {subject, body}
        send.py          # Resend send of one email
        domains.py       # pool selection, caps, warmup curve
        suppress.py      # suppression list read/write
        replies.py       # Zoho IMAP fetch + classify
        suggest_domains.py # Domainr availability suggester
      worker/
        runner.py        # entrypoint: schedule the loops
        tick.py          # one send tick (reads as a list of calls)
        warmup.py        # daily cap reset + ramp
      utils/
        email_format.py  # syntax check, role/disposable detection, dedupe
        text.py          # html -> clean text
        time_window.py   # send-window + timezone helpers
    tests/
  frontend/            # SvelteKit + Tailwind
```

Rule: `api/` never contains business logic; `core/` never imports from `api/`.

---

## 5. Database schema (Supabase Postgres)

Use migrations. All tables have `id`, `created_at`. RLS on (see §10).

### `campaigns`
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| user_id | uuid | owner |
| name | text | |
| status | text | `draft`, `prepping`, `ready`, `sending`, `done`, `paused` |
| sample_approved | bool | review-sample gate passed |

### `contacts`
| column | type | notes |
|---|---|---|
| id | bigint pk | |
| campaign_id | uuid fk | |
| first_name, last_name, company_name, company_website, position, bio | text | from upload |
| email | text | found/uploaded address |
| status | text | state machine, see §6 |
| mv_result | text | MillionVerifier code: `ok`/`catch_all`/`disposable`/`invalid`/`unknown` |
| reject_reason | text | why dropped (auditable) |
| domain_id | uuid fk null | sending domain assigned at send time |

### `contact_enrichments`
`contact_id` fk, `website_content` text.

### `outreach_emails`
`contact_id` fk, `subject`, `body`, `status` (`draft`/`sent`/`bounced`/`replied`),
`resend_message_id`, `sent_at`.

### `sending_domains`
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| domain | text unique | e.g. `getinboxed.com` |
| from_name | text | display name |
| from_locals | text[] | local parts to rotate, e.g. `{joseph, hello, team}` |
| status | text | `warming`, `active`, `paused` |
| warmup_started_on | date | |
| steady_cap_override | int null | overrides default steady cap |

### `domain_daily_stats`
`domain_id` fk, `date`, `sent_count`, `bounce_count`, `complaint_count`.
Unique on (`domain_id`, `date`).

### `responses`
`contact_id` fk, `outreach_email_id` fk null, `imap_uid` text, `reply_body`,
`sentiment` (`positive`/`neutral`/`negative`/`unsubscribe`), `is_hot_lead` bool,
`received_at`.

### `suppressions`
`email` text unique, `reason` (`bounce`/`complaint`/`unsubscribe`), `created_at`.

---

## 6. Contact state machine

```
new
  └─ has email? ── no ──▶ finding ──▶ no_email (drop) | (email found) ─┐
  └─ yes ───────────────────────────────────────────────────────────┤
                                                                       ▼
                                                                   verifying
                                                                       │
                                  mv_result == "ok" ? ── no ──▶ rejected (drop)
                                                       └─ yes ──▶ verified
                                                                       │
                                                                   enriching ──▶ enriched
                                                                       │
                                                                   generating ──▶ drafted
                                                                       │
                                                                    queued
                                                                       │ (send worker)
                                                                    sending ──▶ sent
                                                                       │
        webhook ──▶ bounced | complained        imap ──▶ replied | hot_lead | unsubscribed
```

`rejected`, `no_email`, `bounced`, `complained`, `unsubscribed` are terminal and never
re-processed. Each core function advances a contact exactly one state and writes
`reject_reason` when it drops one.

---

## 7. Core modules — responsibilities and signatures

Signatures are the contract. Keep functions short; extract anything with a section
comment.

### `core/verify.py` — the gate
```python
def verify_email(email: str) -> VerifyResult        # one real-time MillionVerifier call
def is_deliverable(result: VerifyResult) -> bool    # strict: result.code == "ok"
def verify_contact(contact: Contact) -> Contact     # sets mv_result, advances state
```
- MillionVerifier real-time API: `GET https://api.millionverifier.com/api/v3/?api=KEY&email=…`.
- Strict mode keeps only `ok`. `catch_all`, `disposable`, `invalid`, `unknown` →
  `rejected` with `reject_reason = mv_result`.
- Run a free local prefilter first (`utils/email_format`): bad syntax, role addresses
  (`info@`, `sales@`, …), disposable domains, and suppressed addresses are dropped
  **before** spending a MillionVerifier credit.

### `core/finder.py`
```python
def find_email(first: str, last: str, domain: str) -> str | None   # Hunter finder
```
Called only when a contact has no email. No pattern-guessing — if Hunter returns
nothing, the contact goes to `no_email`. (Guessing is what causes bounces.)

### `core/enrich.py`
```python
def scrape_company(url: str) -> str   # homepage + /contact,/about,/team, cleaned, capped
```
Runs only on `verified` contacts.

### `core/generate.py`
```python
def generate_email(contact: Contact, website_text: str) -> Draft | None
```
Use the proven outreach prompt (see Appendix A). Store it in `config.py` as a constant
so it's tweakable, defaulting to the proven version. Append the unsubscribe footer.
Claude `claude-sonnet-4-6`, prompt-cache the system block.

### `core/send.py`
```python
def send_one(domain: SendingDomain, contact: Contact, draft: Draft) -> SendResult
```
- Resend API. `from` = `"{from_name} <{local}@{domain}>"` (rotate `from_locals`).
- `reply_to` = `ZOHO_REPLY_TO`.
- Set `List-Unsubscribe` and `List-Unsubscribe-Post` headers (one-click unsubscribe;
  improves inbox placement).
- On success: write `resend_message_id`, advance to `sent`, increment domain stats.

### `core/domains.py`
```python
def active_domains() -> list[SendingDomain]
def remaining_today(domain: SendingDomain) -> int          # cap_today - sent_today
def cap_today(domain: SendingDomain) -> int                # warmup curve, see §8
def pick_domain(domains: list[SendingDomain]) -> SendingDomain | None  # most remaining
def record_send(domain: SendingDomain) -> None
```

### `core/suppress.py`
```python
def is_suppressed(email: str) -> bool
def suppress(email: str, reason: str) -> None
```

### `core/replies.py`
```python
def fetch_new_replies() -> list[RawReply]      # Zoho IMAP, unseen since last uid
def classify(reply_body: str) -> str           # Claude haiku
def record_reply(reply: RawReply) -> None      # match contact, store, update status
```
Sentiment classes: `positive` / `neutral` / `negative` / `unsubscribe`. A `positive`
reply sets the contact to `hot_lead`; `unsubscribe` suppresses the address.

### `core/suggest_domains.py`
```python
def suggest_sending_domains(base_name: str) -> list[DomainSuggestion]
```
Generate variants (`get-`, `try-`, `-hq`, `.io`, `.co`, `mail-`) and check availability
via the Domainr API. Returns available domains only. Optional — guarded by
`DOMAINR_API_KEY`; the page is hidden if unset. You still register + DNS manually.

---

## 8. Send worker — the autonomous core

### `worker/tick.py` — one tick (default every 15 min)
Reads as a list of calls:
```python
def tick() -> None:
    if not within_send_window():
        return
    for domain in active_domains():
        budget = remaining_today(domain)
        for contact in claim_queued(budget):     # FOR UPDATE SKIP LOCKED
            draft = draft_for(contact)
            result = send_one(domain, contact, draft)
            handle_send_result(contact, result)
            sleep(jitter())                       # human-like spacing
```

### `worker/warmup.py`
```python
def cap_today(domain) -> int
def reset_daily_counts() -> None    # runs at local midnight
```
Warmup curve (all values in env, defaults shown):
```
day = today - warmup_started_on
cap = min(WARMUP_STEADY_CAP, WARMUP_START_CAP + WARMUP_STEP * day)
# defaults: start 20, step 25, steady 250  -> reaches 250 on ~day 10
```
A domain is `warming` until it reaches steady cap, then `active`. Same send logic
either way — only the cap differs.

### Safety auto-pause (the failsafe)
After each tick, for each domain compute rolling 3-day rates from `domain_daily_stats`:
```
if bounce_rate > MAX_BOUNCE_RATE (default 0.03)         -> status = paused
if complaint_rate > MAX_COMPLAINT_RATE (default 0.0005) -> status = paused
```
Buffers sit under Resend's hard limits (4% bounce, 0.08% spam) so the account is never
at risk. Paused domains are surfaced in the UI and require manual reactivation.

### `worker/runner.py`
Entry point for the Render/Railway worker. Schedules three intervals: `tick`
(15 min), `fetch_new_replies` (10 min), `reset_daily_counts` (daily at local midnight).
Use `apscheduler` — the one justified dependency; it replaces a hand-rolled loop and is
standard.

### Throughput check (1-month / 100k target)
18 domains, 14-day ramp (20→250), steady 250/day:
- Ramp phase contributes tens of thousands; steady phase 18 × 250 = 4,500/day.
- 100k is reached comfortably within ~30 days. 15–20 domains is the right pool size.
The single lever for speed is **domain count** — everything else is fixed by
deliverability physics.

---

## 9. API surface (FastAPI)

Thin routers; each calls one core function. SSE only where live progress helps.

```
POST   /api/campaigns                      create campaign
POST   /api/campaigns/{id}/upload          ingest CSV/XLSX -> contacts
POST   /api/campaigns/{id}/prep            run prep pipeline (SSE progress)
GET    /api/campaigns/{id}/sample          N generated emails for review
POST   /api/campaigns/{id}/launch          set status=sending (worker takes over)
POST   /api/campaigns/{id}/pause

GET    /api/campaigns/{id}/stats           counts by state + replies + hot leads
GET    /api/domains                        pool + warmup progress + paused flags
POST   /api/domains                        add a domain to the pool
POST   /api/domains/suggest                Domainr suggestions for a base name

POST   /api/webhooks/resend                bounce/complaint/delivered -> suppress + stats
```
Verify the Resend webhook signature (`RESEND_WEBHOOK_SECRET`).

---

## 10. Auth (Supabase Auth)

- Supabase Auth, email + password (magic link optional). Frontend uses `supabase-js`.
- Backend validates the Supabase JWT on every `/api/*` route except the webhook.
- RLS: all tenant tables filter by `user_id` (or `campaign.user_id` via join). Single
  org for now; the `user_id` column makes multi-tenant a later config change, not a
  rewrite. Service-role key is backend-only and bypasses RLS for the worker.

---

## 11. Frontend — editorial step flow

Not a dashboard. No nav bar, no sidebar, no menus. A calm, light, vertical
**guided flow** of minimal cards separated by hairline rules — closer to a Linear/Notion
onboarding or an editorial page than an admin panel.

Visual language:
- Light theme, generous whitespace, `1px` neutral borders, no heavy shadows.
- Cards/boxes with a clear single purpose; thin progress lines for warmup/verify.
- One accent color, used sparingly. System font stack. Tailwind utilities only.

The flow (each a step):
1. **Upload** — drop CSV/XLSX, confirm column mapping, see contact count.
2. **Verify** — run the gate; live card shows kept vs dropped and the credit cost.
3. **Review sample** — a statistically significant sample of generated emails as clean
   preview cards. Primary action: **Approve all**. Secondary: skim/skip individual,
   or **Skip review** entirely.
4. **Domains** — pool cards with warmup progress lines and paused flags; add-domain and
   suggest-domain live here.
5. **Launch & monitor** — confirm, then a quiet status page: cards for sent today,
   total sent, replies, hot leads, and per-domain progress. Updates while you sleep.

Components are small and reused: `Card`, `StepHeader`, `StatPill`, `ProgressLine`,
`DomainCard`, `EmailPreviewCard`, `DropZone`. Each does one thing.

---

## 12. External services & APIs

| Purpose | Service | Notes |
|---|---|---|
| Verify (gate) | **MillionVerifier** real-time API | strict `ok`; ~$0.0005/email |
| Find missing emails | **Hunter** email-finder | only when email missing |
| Generate | **Anthropic** Claude | proven prompt (Appendix A) |
| Send | **Resend** | multi-domain, webhooks for bounce/complaint |
| Replies | **Zoho** IMAP | reply-to a Zoho mailbox; poll via `imaplib` |
| Domain suggestions | **Domainr** | optional |
| DB + Auth + queue | **Supabase** | Postgres is the queue |
| Hosting | **Render or Railway** | API service + always-on worker |

Replies note: Resend inbound is **not** used — it needs the domain's MX pointed at
Resend, which conflicts with Zoho. Replies come back to the Zoho mailbox; we poll IMAP.

---

## 13. Deploy (Render / Railway)

Two processes from one repo:
- **web** — `uvicorn app.main:app` (the API).
- **worker** — `python -m app.worker.runner` (the autonomous loops).

Frontend deploys as a static SvelteKit build (Render static site / Vercel / Netlify).
All secrets via the host's env panel; never commit `.env`. This cloud-hosted shape is
what makes Inboxed sellable as a hosted product.

---

## 14. Testing (required, iterative — not at the end)

- `utils/email_format`: unit tests for syntax/role/disposable detection.
- `core/verify`: mock MillionVerifier; assert strict gate keeps only `ok`.
- `core/domains` + `worker/warmup`: cap curve, remaining-today, auto-pause thresholds.
- `worker/tick`: with a seeded DB, assert it respects caps and the send window and never
  exceeds budget.
- **Accuracy spike before full build**: run a few hundred addresses from a known-bounced
  list through MillionVerifier; confirm the bounced ones return `invalid`/`catch_all`.
  Validates the gate on real data for ~$5.

---

## 15. Out of scope (deliberately)

A/B testing, drip sequences, an analytics dashboard, CRM sync, team roles, dedicated-IP
management UI. Add only if a real need appears.

---

## Appendix A — Generation prompt (proven)

System:
```
You are an expert B2B sales copywriter specializing in AI integration for enterprises.
Your job is to write concise, hyper-personalized cold outreach emails (under 150 words total).

The sender's company helps businesses identify and solve specific AI integration gaps — from
automating manual workflows, to building AI-powered customer experiences, to integrating LLMs
into existing products.

Rules:
- Never use generic AI buzzwords like "leverage", "revolutionize", "transform", "game-changer"
- Reference something specific about the prospect's actual role, company, or bio
- Identify a concrete, plausible AI pain point for their specific context
- Keep paragraphs to 1-2 sentences each
- End with a single soft CTA (e.g. "Would a 20-minute call make sense?")
- Return only valid JSON, no markdown wrapping
```
User template: prospect name/role/company/website + bio + scraped website excerpt, then:
`Return JSON only: {"subject": "under 8 words, personalized", "body": "3 short paragraphs under 150 words"}`

Generalize the "AI integration" framing to a configurable value proposition later — but
ship with this version, since it earned strong replies.
