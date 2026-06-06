# Inboxed — Setup

Everything you must configure once before the system runs. Do these in order. All
secrets go in `.env` (backend) and the frontend `.env` — never commit them.

---

## 1. Supabase (database + auth)

1. Create a project.
2. Run the migrations in `migrations/` to create the tables in `SPEC.md §5`.
3. Enable **Email** auth (Authentication → Providers). Password or magic link.
4. Turn on **RLS** for all tenant tables; policies filter by `user_id`.
5. Copy into `.env`: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (service role — backend
   only), and `SUPABASE_ANON_KEY` (frontend).

## 2. MillionVerifier (the verification gate)

1. Sign up, grab the API key at `app.millionverifier.com/api`.
2. Buy the smallest credit pack — credits never expire.
3. **Accuracy spike (do this first):** run a few hundred addresses from a known-bounced
   list through the real-time API. Confirm the ones that actually bounced come back
   `invalid`/`catch_all`. This proves the gate on real data for ~$5.
4. Set `MILLIONVERIFIER_API_KEY`.

## 3. Hunter (only for contacts missing an email)

1. Get an API key from hunter.io.
2. Set `HUNTER_API_KEY`. Used only when an uploaded row has no email; if your lists
   already include emails, this is barely touched.

## 4. Anthropic (generation + reply classification)

Set `ANTHROPIC_API_KEY`. Models: `claude-sonnet-4-6` (generate),
`claude-haiku-4-5` (classify replies).

## 5. Sending domains (Resend) — the important one

Do **not** send cold from your primary company domain or its subdomains — cold
complaints contaminate the reputation of your real mail. Register **15–20 separate
dedicated domains** for cold sending. Use the in-app suggester (Domainr) to find
available variants, then buy them at any registrar.

For **each** domain:
1. Add it in Resend (Domains → Add).
2. Add the SPF, DKIM, and DMARC DNS records Resend gives you, at your registrar.
3. Wait for Resend to verify the domain.
4. Add a row to `sending_domains` (via the app): `domain`, `from_name`, `from_locals`.
   New domains start in `warming` and ramp automatically (SPEC §8).

Set `RESEND_API_KEY`. Create a webhook (Resend → Webhooks) pointed at
`https://<your-api-host>/api/webhooks/resend` for `email.bounced`, `email.complained`,
`email.delivered`; put its signing secret in `RESEND_WEBHOOK_SECRET`.

> Warm domains in parallel starting day one. With ~18 domains, 100k verified contacts
> sends within roughly a month. Speed scales with domain count and nothing else.

## 6. Zoho (reply tracking)

Replies return to a Zoho mailbox (your domain's MX points at Zoho). Resend inbound is
**not** used — it would require pointing MX at Resend, conflicting with Zoho.

1. In Zoho Mail, enable **IMAP** and create an **app-specific password**.
2. Set `ZOHO_IMAP_HOST` (`imap.zoho.com`), `ZOHO_IMAP_USER`, `ZOHO_IMAP_PASSWORD`
   (the app password), and `ZOHO_REPLY_TO` (the address used as `reply_to` on sends).

## 7. Domainr (optional — sending-domain suggester)

Get a Domainr API key (via RapidAPI) and set `DOMAINR_API_KEY`. If unset, the suggest
feature is hidden; everything else works.

## 8. Deploy (Render or Railway)

Two processes from this repo:
- **web:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **worker:** `python -m app.worker.runner` (always-on; the "while you sleep" part)

Frontend: build the SvelteKit app as a static site (Render static / Vercel / Netlify).
Set all env vars in the host's dashboard. Point the Resend webhook at the deployed
web URL.

---

## Tuning (env, optional)

| Var | Default | Meaning |
|---|---|---|
| `WARMUP_START_CAP` | 20 | day-1 sends per domain |
| `WARMUP_STEP` | 25 | cap increase per day |
| `WARMUP_STEADY_CAP` | 250 | steady per-domain daily cap |
| `MAX_BOUNCE_RATE` | 0.03 | auto-pause a domain above this (Resend hard limit 0.04) |
| `MAX_COMPLAINT_RATE` | 0.0005 | auto-pause above this (Resend hard limit 0.0008) |
| `SEND_WINDOW_START` / `_END` | 8 / 18 | local send hours |
| `SEND_TIMEZONE` | America/New_York | window timezone |

Leave defaults unless deliverability data says otherwise.
