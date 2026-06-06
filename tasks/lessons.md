# Inboxed — Lessons

Patterns learned from corrections and incidents. Review at session start.

## Never send to an unverified address
An earlier outreach build guessed addresses (`first.last@domain`) and sent without
verification. Result: ~50% bounce on a 6k run — and Resend pauses any account over 4%
bounce. **Rule:** verification is a hard gate. Keep only MillionVerifier `ok`. No
pattern-guessing anywhere. If an email can't be found or verified, drop the contact.

## Spend nothing before the gate
Hunter, Claude, and Resend all cost money/credits. **Rule:** order the pipeline so
verification runs before any paid step. Enrich and generate only on verified contacts.

## Cold sending is a domain-count problem, not a tooling problem
Per-domain cold volume is capped by inbox providers and Resend's spam limit. **Rule:**
scale throughput with more warmed domains, never by sending more per domain. Never send
cold from the primary domain or its subdomains.

## Resend inbound conflicts with Zoho
Resend inbound needs MX pointed at Resend; the domain's MX points at Zoho. **Rule:**
track replies via Zoho IMAP, not Resend inbound.
