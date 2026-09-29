# Cost and lock-in — round 1

Accessed: 2026-09-23. Pricing figures below are from official pages fetched live this run; page visible dates were not shown on those pages → **pub_date unknown** unless noted. Stale composites (Acquaint Softtech 2026-05-15; MarsDevs April 2026) were not used.

## Findings

### Smallest paid tiers used (validation: 5–10 brokerages, thousands of listings, daily email)

| Component | Smallest paid (or free if sufficient) | Source |
| --- | --- | --- |
| Supabase | **Pro $25/mo** org + compute per project (Micro **~$10/mo**; Pro includes **$10** compute credits) | supabase.com/pricing |
| Vercel | **Pro $20/mo** (Hobby free is non-commercial) | vercel.com/pricing |
| Railway (alt: app + Postgres + Redis) | **Hobby $5/mo** ($5 usage included) or **Pro $20/mo** ($20 usage); usage: ~$10/GB-mo RAM, ~$20/vCPU-mo, $0.15/GB-mo volumes | railway.com/pricing |
| Job runner | Trigger.dev **Hobby $10/mo** (Free = $0 + $5 credits; FAQ: tasks have **no timeouts**) | trigger.dev/pricing |
| Email | Resend **Free $0** (3,000 emails/mo, 100/day) covers ~5–10 daily digests; smallest paid **Pro $20** (50k emails) | resend.com/pricing |
| Redis (Railway path) | No separate SKU — Redis as a Railway service at memory/CPU rates above | railway.com/pricing |
| Managed Postgres separate | Not fetched this round beyond Railway volumes (Fly MPG searched, not fetched → omitted from totals) | — |

### Arithmetic — Stack A: Next.js on Vercel + Supabase + Trigger.dev + Resend

Assume Resend Free for validation digests (≤100 emails/day); Trigger Hobby paid; one deploying Vercel seat.

**(a) One shared Supabase project (1× Micro)**

- Vercel Pro: $20  
- Supabase: $25 (Pro) + $10 (Micro) − $10 (credits) = **$25**  
- Trigger.dev Hobby: $10  
- Resend Free: $0  

**Subtotal (a) = 20 + 25 + 10 + 0 = ~$55/mo**  
(If Resend Pro: +$20 → **~$75/mo**)

**(b) Ten dedicated small Supabase projects (10× Micro)**

- Supabase: $25 + (10 × $10) − $10 credits = $25 + $100 − $10 = **$115**  
- Vercel $20 + Trigger $10 + Resend $0 = **$30**  

**Subtotal (b) = 115 + 30 = ~$145/mo**  
(If Resend Pro: **~$165/mo**)

Supabase’s own 2-project example confirms the credit math: `$25 + $10 + $10 − $10 = $35` for two Micros.

### Arithmetic — Stack B: app + one Postgres + Redis on Railway (no Supabase/Vercel/Trigger)

Rough continuous services (order-of-magnitude from Railway rates only; not a quote):

- App: 0.5 vCPU + 1 GB RAM ≈ $10 + $10 = **$20**  
- Postgres: 0.5 vCPU + 1 GB + 20 GB volume ≈ $10 + $10 + $3 = **$23**  
- Redis: ~0.25 GB RAM ≈ **$2.50**  
- Usage sum ≈ **$45.50**; Pro plan $20 includes $20 usage → bill ≈ $20 + ($45.50 − $20) = **~$45.50/mo** shared (+ Resend $0)

**(b) Ten dedicated Postgres services:** 10 × ~$23 ≈ **$230** + app $20 + Redis $2.50 → usage ≈ **$252.50**; with Pro credit → **~$252.50/mo** (plus Resend).

### Exit cost

- **Supabase → self-hosted / dump path:** Official guide documents `supabase db dump` for roles/schema/data including RLS and `auth.users`; JWT secrets must be regenerated (users re-auth); OAuth/SMTP reconfigured; **storage objects and edge functions are explicitly not covered** — non-trivial ops work, but a written migration path exists (pub_date unknown on page). Leaving Auth/RLS/storage for *vanilla* Postgres (no GoTrue/storage-api) is **not** fully specified on that page alone → expect app-level auth rewrite + separate object copy; evidence for full vanilla exit is **partial**.  
- **Leaving Vercel:** No dated migration write-up fetched this run → **exit evidence thin** (redeploy Next.js elsewhere is generic; platform lock-in is mainly Functions/Edge/config, not evidenced as a priced exit here).

### Playwright / scraping vs job limits

Vercel Functions are hard-capped (Hobby max **300s**; Pro max **800s**, extended **1800s** beta); Trigger.dev states tasks run with **no timeouts** on managed workers — so browser scrapes fit a long-running managed-job/worker model far better than default serverless function limits.

## Claims

1. Supabase Pro from $25/mo; Micro compute ~$10/mo; Pro/Team include $10/mo compute credits; extra projects add full compute; 2× Micro example = $35/mo; URL: https://supabase.com/pricing; publisher: Supabase; pub_date: unknown; accessed 2026-09-23; confidence: high; class: cost.
2. Vercel Pro $20/mo (Hobby free); URL: https://vercel.com/pricing; publisher: Vercel; pub_date: unknown; accessed 2026-09-23; confidence: high; class: cost.
3. Railway Hobby $5 / Pro $20 with matching included usage; RAM ~$10/GB-mo, CPU ~$20/vCPU-mo, volumes $0.15/GB-mo; URL: https://railway.com/pricing; publisher: Railway; pub_date: unknown; accessed 2026-09-23; confidence: high; class: cost.
4. Trigger.dev Hobby $10/mo; Free $5 credits; compute billed per-second + $0.000025/run; FAQ: tasks have no timeouts; URL: https://trigger.dev/pricing; publisher: Trigger.dev; pub_date: unknown; accessed 2026-09-23; confidence: high; class: cost|implementation.
5. Resend Free 3,000 emails/mo (100/day); Pro from $20/mo for 50,000; URL: https://resend.com/pricing; publisher: Resend; pub_date: unknown; accessed 2026-09-23; confidence: high; class: cost.
6. Platform→self-hosted restore dumps schema/data/RLS/`auth.users`; storage objects and edge functions not covered; JWTs invalidated; URL: https://supabase.com/docs/guides/self-hosting/restore-from-platform; publisher: Supabase; pub_date: unknown; accessed 2026-09-23; confidence: medium; class: implementation.
7. Vercel Function duration: Hobby max 300s; Pro max 800s / 1800s beta; URL: https://vercel.com/docs/functions/configuring-functions/duration; publisher: Vercel; pub_date: unknown; accessed 2026-09-23; confidence: high; class: implementation.

## Leads

- Fetch Fly.io Managed Postgres pricing page live for a second “10 dedicated DBs” comparator ($38 Basic appeared in search only — inadmissible until fetched).
- Inngest pricing page (Hobby $0 / Pro $99 in search) as Trigger.dev alternate.
- Postmark / AWS SES pricing for email cost floor vs Resend.
- Upstash Redis fixed plans if Redis is not co-located on Railway.
- Better Auth / WorkOS Supabase Auth migration guides for vanilla-Postgres auth exit (vendor docs; date-check needed).
- Vercel Workflows (unlimited pause/resume) for scrape orchestration without Trigger.dev.

## Not found

- Visible publication dates ≥ 2026-06-23 on the fetched pricing pages (all marked unknown).
- Migration write-up dated ≥ 2025-09-23 specifically for leaving Vercel.
- End-to-end guide for exiting Supabase Auth/RLS/Storage to vanilla Postgres only (restore guide is self-hosted Supabase stack, not vanilla).
- Official Hetzner/DigitalOcean VPS price snapshot this run.
- Fly.io / Neon / Inngest / SES pages fetched within budget (8-page cap).
