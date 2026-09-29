# Implementation reality — round 1

Access date: 2026-09-23. Freshness gate: prefer signals on or after 2026-03-23; older material marked low and not used to rank stacks.

## Findings

Round-1 fresh retrospectives with numbers that map cleanly onto “dashboard + background jobs” are thin. The strongest solo production write-up in scope is Faysal’s Django + React + Celery + Postgres SaaS (dated 2026-03-23, updated 2026-04-09): months to MVP, 50k+ LOC, 30+ Celery task types, mandatory ORM tenant scoping with leakage tests, and an explicit regret that dual Django/React deploy pipelines added overhead. That is self-hosted queue burden, not vendor queue burden.

For Next.js + managed runners, the fresh record is vendor incidents, not solo founder postmortems. Trigger.dev’s 2026-06-22 incident report documents multi-hour / ~day-scale dequeue outages across us-east-1 then eu-central-1, impacting tens of thousands of orgs, with concurrency locked to degraded regions and painful region switching—work was not lost but lag was long. That is operational risk transferred to the job SaaS, not evidence that Next+Supabase is easy for a solo scraper product.

Laravel signal (2026-09-13): Deploynix argues solo/small apps with one modest queue should stay on plain `queue:work` under Supervisor; Horizon adds Redis-only coupling, dashboard auth surface, and monitor-the-monitor overhead. That is the lightest *cited* solo ops posture among stacks that actually appear in 2026 production writing—but it is an ops essay, not a full product retrospective with incident metrics.

Scraper/API isolation: Celery’s Workers Guide models workers as separately started (and daemonized) processes; Routing docs show dedicating a machine/worker to a feed queue via `-Q feeds` so feed work does not share a consumer with default tasks. Together that supports (a) browser/scraper crashes killing a worker process without taking down a separate HTTP process, and (b) per-source queue isolation so one broken site’s backlog/retries do not starve other queues—if you route and pin workers that way. No fresh Playwright-in-production SaaS retrospective with crash numbers was retrieved.

Auth isolation burden: Tomoda (2026-06-24) is a production-shaped Supabase RLS account (69 tables, 280 policies, pgTAP allow+deny CI). Burden is continuous policy testing and SECURITY DEFINER pitfalls—not a head-to-head with Django/Laravel `tenant_id`. Faysal’s Django side is app-enforced tenant filters + leakage tests (same author stack as above). Direct “RLS vs tenant_id months later” comparative retrospective not found.

Email: provider/docs and 2026 digest-ops essays agree digests are at-least-once; FIFO-style short dedup windows do not cover DLQ redrive hours later; Resend documents optional idempotency keys retained 24h. Gotcha: retry/redrive without a durable business key (and/or provider idempotency) duplicates the digest.

Rails and FastAPI full-page retrospectives: not secured this round (Hassan Raza FastAPI+Celery+Render five-service solo lessons appeared in search snippets but the full fetch timed out—lead for round 2).

## Claims

Solo Django+Celery SaaS with dashboard and heavy Celery use: months full-time to MVP; 50k+ LOC; 40+ tables; 100+ endpoints; 30+ Celery task types; 99.9%+ uptime claim; multi-tenancy via mandatory ORM tenant filter + leakage tests; regrets dual frontend/backend deploy overhead and launching five integrations at once; uses Resend for email.; https://byfaysal.com/blog/i-built-hootsuite-competitor-solo; by Faysal; 2026-03-23 (updated 2026-04-09); accessed 2026-09-23; confidence high; class implementation.

Managed Trigger.dev cloud: us-east-1 then eu-central-1 slow dequeue / full outages ~2026-06-22 19:00 UTC through ~2026-06-23 13:13 UTC; tens of thousands of orgs impacted; no runs lost but long delays; concurrency accounting locked queued runs to degraded region; recovery/backpressure/multi-cluster fixes planned or partial.; https://trigger.dev/blog/incident-report-jun-22-2026; Trigger.dev; 2026-06-22; accessed 2026-09-23; confidence high; class landscape.

Laravel solo/small production guidance: plain Supervisor `queue:work` sufficient for one queue / light workload; Horizon justified mainly for multi-queue Redis workloads needing auto-balance and dashboard retries; Horizon adds Redis requirement, dashboard gating, and Horizon as SPOF for the worker pool.; https://deploynix.io/blog/do-you-need-laravel-horizon; Deploynix; 2026-09-13; accessed 2026-09-23; confidence medium; class implementation.

Celery workers are separately started OS processes (daemonizable); multiple named workers supported; KILL of a stuck worker terminates that worker (and can lose in-flight tasks unless acks_late), independent of an HTTP server process if deployed separately.; https://docs.celeryq.dev/en/latest/userguide/workers.html; Celery Project; docs for Celery 5.6.2 (living docs, retrieved 2026-09-23); accessed 2026-09-23; confidence high; class landscape.

Celery routing: route feed/import-style tasks to a dedicated queue and start a worker with `-Q feeds` (or feeds+default) so one class of work is isolated on its own consumer(s).; https://docs.celeryq.dev/en/stable/userguide/routing.html; Celery Project; Celery 5.6.x docs; accessed 2026-09-23; confidence high; class landscape.

Supabase RLS production burden: author ships Expo+Next.js+Supabase with RLS on 69 public tables and 280 policies; argues RLS is only trustworthy with pgTAP allow+deny CI; cites recurring failure modes (missing WITH CHECK, deny paths untested, SECURITY DEFINER holes).; https://tomodahinata.com/en/blog/supabase-rls-testing-pgtap-policy-regression-guide; Tomoda Hinata; 2026-06-24; accessed 2026-09-23; confidence high; class implementation.

Daily/weekly digest email gotcha: queue delivery is at-least-once; FIFO-style ~5-minute transport dedup does not protect operator DLQ redrive hours later; durable business idempotency key required before send.; https://dev.to/jamesanderson121/weekly-digest-retries-fifo-vs-standard-queues-and-idempotent-duplicate-handling-4emb; DEV Community (James Anderson); undated in snippet / 2026-week examples in body; accessed 2026-09-23; confidence medium; class implementation.

Resend: optional idempotency keys on send/batch; same key within 24h returns prior result without re-sending—operational aid for digest retries.; https://resend.com/docs/dashboard/emails/idempotency-keys; Resend; living docs retrieved 2026-09-23; accessed 2026-09-23; confidence high; class landscape.

## Leads

- https://hassanr.com/blogs/building-two-ai-saas-solo-developer-lessons-2026.html — search synthesis: FastAPI + Celery + Redis, five Render services (1 API + 4 workers), 5–6 months vs 3-month estimate, long jobs 2–4 hours; full WebFetch timed out this round.
- https://opexia.io/insights/lessons-building-solo-healthcare-saas-mealcircle — Celery overkill for daily analytics (3–4 weeks wasted); date/freshness not verified on full page.
- https://zenn.dev/ty1110/articles/6bc189405c69c7 — RLS join policy caused 4.4s count; CI/pgTAP retrospective; verify pub_date and English completeness.
- https://notesonlaravel.com/laravel-horizon-forge-queue/ — solo Forge worker vs Horizon (2026-03-21, just before freshness gate—use only as supporting).
- https://cadence.withremote.ai/blog/supabase-review — 2026 SaaS review of RLS silent failures; verify whether retrospective vs consulting marketing.

## Not found

- Post-2026-03-23 solo/small-team retrospective with queue-lag or incident numbers for Next.js + Supabase + Trigger/Inngest *as the product team’s own ops story* (vendor Trigger incident is not a customer retrospective).
- Rails-fluent solo SaaS 6–12 month retrospective in this pass.
- Full text of Hassan Raza FastAPI stack lessons (fetch timeout).
- One engineering source that explicitly measures Playwright/browser OOM/crash killing an in-process API vs surviving with a separate worker (inference from Celery process model only).
- Direct retrospective comparing months of Supabase RLS ops vs Django/Laravel app-level `tenant_id` (only adjacent singles).
- Inngest-specific production retrospective in this pass.
