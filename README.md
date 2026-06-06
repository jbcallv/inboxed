# Inboxed

Verified, personalized cold email — sent autonomously across a warmed domain pool.

## Quickstart

### 1. Clone and configure

```sh
cp .env.example backend/.env
# fill in all secrets (see SETUP.md)
```

### 2. Database

Run the three migrations in `migrations/` against your Supabase project in order:
- `001_schema.sql` — tables
- `002_rls.sql` — row-level security policies
- `003_functions.sql` — `claim_queued_contacts` and `increment_domain_stat`

### 3. Backend (API + worker)

```sh
cd backend
uv sync
uv run uvicorn app.main:app --reload      # API on :8000
uv run python -m app.worker.runner        # autonomous worker
```

### 4. Frontend

```sh
cd frontend
cp .env.example .env
# fill in VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL
npm install
npm run dev                               # dev server on :5173
```

### 5. Tests

```sh
cd backend
uv run pytest -v
```

## Architecture

Two processes, one Postgres database (Supabase):

- **API** (`uvicorn app.main:app`) — thin FastAPI routers, delegate to `core/`
- **Worker** (`python -m app.worker.runner`) — send tick (15 min), reply poller (10 min), daily warmup reset (midnight)

The send tick uses `SELECT … FOR UPDATE SKIP LOCKED` (via Postgres function `claim_queued_contacts`) so multiple workers can run safely.

## Key constraints (from SPEC)

- Verification is a hard gate — only `MillionVerifier ok` passes. No pattern-guessing.
- No credit (Hunter/Claude/Resend) is spent before verification.
- Throughput scales with domain count, not with config. 18 domains → ~4 500/day at steady state.
- Replies tracked via Zoho IMAP (not Resend inbound — MX conflict).

## Credential verification needed (requires live keys)

- MillionVerifier accuracy spike — run ~200 known-bounced addresses, confirm gate holds
- Hunter email finder — verify domain/name lookup returns results
- Resend webhook signature — test with a real bounce event
- Zoho IMAP — test unseen fetch and Seen flag marking
- Supabase JWT validation — test with a real auth session token

See `SETUP.md` for the full setup checklist.
