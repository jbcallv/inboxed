# Inboxed

Autonomous cold email — verified, personalized, and sent across a warmed domain pool.

## Setup

### 1. Environment

```sh
cp .env.example backend/.env
# fill in keys: SUPABASE_URL, SUPABASE_SERVICE_KEY, ANTHROPIC_API_KEY,
#               HUNTER_API_KEY, RESEND_API_KEY, ZOHO_IMAP_USER, ZOHO_IMAP_PASSWORD
```

### 2. Database

Run migrations against your Supabase project in order:

```
migrations/001_schema.sql
migrations/002_rls.sql
migrations/003_functions.sql
```

Paste each file into the Supabase SQL editor and run.

### 3. Frontend env

```sh
cp frontend/.env.example frontend/.env
# fill in VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL=http://localhost:8000
```

## Running locally

```sh
# backend
cd backend && uv sync
uv run fastapi dev app/main.py        # API on :8000

# worker (separate terminal)
uv run python -m app.worker.runner    # ticks every 15 min

# frontend (separate terminal)
cd frontend && npm install && npm run dev   # UI on :5173
```

## Campaign flow

1. Create a campaign at `/campaigns`
2. Upload a CSV of contacts (needs `first_name`, `last_name`, `company_website` at minimum)
3. Run **Verify + generate** — Hunter finds missing emails, Claude drafts each one
4. Review the sample to confirm email quality
5. Add a sending domain (must be verified in Resend with SPF/DKIM/DMARC)
6. Launch — the worker picks up queued contacts and sends automatically

## Testing the send pipeline locally

Pause the Railway worker first (so it doesn't race your local process), then:

```sh
cd backend
uv run python -m app.worker.run_tick_once   # fires one tick immediately, no window check
```

## Tests

```sh
cd backend && uv run pytest -v
cd frontend && npm test
```

## Deployment

Deployed on Railway. `main` branch auto-deploys via `Procfile`:

```
web:    uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: uv run python -m app.worker.runner
```
