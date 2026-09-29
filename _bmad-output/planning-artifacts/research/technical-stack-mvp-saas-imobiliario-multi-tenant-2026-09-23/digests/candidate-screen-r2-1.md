# Candidate screen — round 2

Access date: 2026-09-23. Screening cutoff: published on or after 2026-03-23. Round-1 URLs were not re-fetched.

## Findings

### 1. Model A — shared catalog + tenant-private overlays

Microsoft’s Azure Database for PostgreSQL elastic-clusters multitenant tutorial (`ms.date` 2026-07-08) documents a primary engineering pattern that maps cleanly onto Model A’s *shared corpus*: tenant-scoped tables are distributed by `company_id`, while data that “naturally belong[s] to all tenants” is modeled as a **reference table** (`geo_ips`) via `create_reference_table`, synchronized on every worker node and joined by all tenants without a tenant ownership column on the shared rows ([Microsoft Learn / MicrosoftDocs](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/tutorial-multitenant-database); source metadata `ms.date: 07/08/2026`).

ADHDecode (2026-04-16) shows the same split in application form for FastAPI/PostgreSQL: tenant-private tables live under per-tenant schemas, while shared resources fall back to the `public` schema via `SET search_path TO {schema_name}, public` ([ADHDecode](https://adhdecode.com/articles/fastapi/fastapi-multi-tenancy-implementation/)). That is the “global rows + tenant overlay” shape for radars/favorites/alerts (overlays in tenant schemas; catalog in shared/public), even though the article’s example overlay is `items` rather than saved searches.

**RLS fit.** Acquaint Softtech’s shared-schema model (2026-05-15) assumes isolation via a `tenant_id` column “on each table” plus RLS ([Acquaint Softtech](https://acquaintsoft.com/blog/multi-tenant-saas-architecture-guide)). Microsoft’s reference-table catalog has **no** `company_id` / `tenant_id` on the shared rows. A naive “every table has `tenant_id` + RLS” template is therefore a **poor fit** for the shared listing corpus unless the catalog uses a different policy (e.g. public-read / no tenant predicate) while overlays keep tenant-scoped RLS. No retrieved source used the exact phrase “bad fit,” but the two patterns contradict each other on whether every table carries `tenant_id`.

### 2. Model B — per-tenant databases / duplicated collection

Acquaint Softtech (2026-05-15), citing composites from production SaaS delivery 2022–2026, maps Model B’s isolation story directly: blast radius of a heavy query, runaway job, or compromised credentials is **everyone** on a shared database and **one tenant** on database-per-tenant; at “Small (50 tenants)” they quote database-per-tenant at **$2,000–$4,500/mo infra and 4–8 hrs/wk DevOps** versus shared schema **$400–$900/mo** with minimal DevOps ([Acquaint Softtech](https://acquaintsoft.com/blog/multi-tenant-saas-architecture-guide)). They also state per-tenant DB overhead is “invisible” at ~50 tenants but dominates at 5,000, and that starting database-per-tenant on day one with few tenants is common over-engineering. For a validation band of ~5–10 brokerages, that evidence supports Model B as **affordable and strong on blast radius**, with ops load already material (hours/week) even before “low hundreds.”

For **duplicated collection over the same public sources**, NHI Mgmt Group (updated 2026-09-10) compares per-tenant vs shared scraping (telemetry/log controllers, analogous to scrape jobs): per-tenant scraping isolates blast radius and fairness; shared scraping is simpler but creates noisy-neighbor and contention risks; per-tenant designs raise lifecycle/ops overhead ([NHI Mgmt Group](https://nhimg.org/faq/what-is-the-difference-between-per-tenant-log-scraping-and-shared-log-scraping-i/)). No fresh source was found that measures dollar cost of *duplicated scrapes of the same real-estate sites* at 5–10 tenants specifically.

### 3. FastAPI + PostgreSQL + background workers (multi-tenant)

**Not found** as a single source published on or after 2026-03-23 that names all of: FastAPI, PostgreSQL, background workers, and multi-tenancy.

Near-misses (not used as a positive answer to Q3): Ugur Aslim (2026-06-14) — FastAPI multi-tenant + background tasks (`asyncio.create_task`) + SQLAlchemy, but does not name PostgreSQL ([uguraslim.com](https://uguraslim.com/blog/fastapi-async-context-vars-for-multi-tenant-request-isolatio/)); ADHDecode (2026-04-16) — FastAPI + PostgreSQL multi-tenant schema isolation, no workers; FastAPI Patterns ARQ guide — FastAPI + separate ARQ worker process + `asyncpg`/database pool language, not a multi-tenant production account.

### 4. Schema-per-tenant — production ops account

Nas (@itsnas), **2026-09-12**, is a production-ops account of schema-/database-per-tenant migration pain at **hundreds** of tenants: migrations must succeed N times; partial failure leaves fleet split (example: tenant 247 of 500); need a tenant registry, per-tenant migration ledger, throttled concurrency, wave rollouts, expand-contract deploys, and drift detection ([itsnas.me](https://itsnas.me/writing/migrating-schema-per-tenant-databases-at-scale)). This **supports the pain side**, not a “works cleanly at tens-to-hundreds without extra infrastructure” claim. Zero-Downtime Schema’s multi-tenant migration guide adds mechanism detail (catalog pressure, `max_locks_per_transaction`, fleet version as a distribution) but lacked a clear first-party pub_date in the fetched page; treated as supporting landscape only if dated independently.

### 5. Per-source / process isolation for scrapers (budget remnant)

FastAPI Patterns’ ARQ + FastAPI guide states the worker is a **separate process** with its own pools; the API and worker share Redis only—so a worker-side crash/failure domain is isolated from the HTTP process, and jobs are retried via `max_tries` rather than taking down the API ([fastapi-patterns.com](https://fastapi-patterns.com/async-background-tasks-observability/background-task-processing/running-arq-workers-with-fastapi/)). Pub date not visible on the fetched page → **low freshness** for screening; mechanism claim only. NHI (2026-09-10) supports per-tenant collection lanes for blast-radius containment of scrape-like workloads (see §2).

## Claims

1. Shared multi-tenant Postgres designs can hold globally shared rows in reference/shared tables while tenant data is sharded by tenant key; maps to Model A shared listing corpus. Source: https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/tutorial-multitenant-database ; publisher: Microsoft; pub_date: 2026-07-08 (`ms.date`); accessed 2026-09-23; confidence: high; class: pattern.

2. FastAPI/PostgreSQL can keep shared tables in `public` and tenant-private tables in per-tenant schemas via `search_path`; maps to Model A catalog + overlays. Source: https://adhdecode.com/articles/fastapi/fastapi-multi-tenancy-implementation/ ; publisher: ADHDecode; pub_date: 2026-04-16; accessed 2026-09-23; confidence: medium; class: implementation.

3. Shared-schema RLS guidance that puts `tenant_id` on every table conflicts with a shared catalog that has no tenant column; Model A needs hybrid policies. Source: https://acquaintsoft.com/blog/multi-tenant-saas-architecture-guide (tenant_id-on-each-table shared model) contrasted with Microsoft reference tables above; publisher: Acquaint Softtech / Microsoft; pub_date: 2026-05-15 / 2026-07-08; accessed 2026-09-23; confidence: medium; class: pattern.

4. Database-per-tenant confines blast radius to one tenant; shared DB blast radius is all tenants. Source: https://acquaintsoft.com/blog/multi-tenant-saas-architecture-guide ; publisher: Acquaint Softtech; pub_date: 2026-05-15; accessed 2026-09-23; confidence: high; class: pattern.

5. At ~50 tenants, database-per-tenant composites cite ~$2,000–$4,500/mo infra and 4–8 hrs/wk DevOps vs ~$400–$900/mo shared schema. Source: same Acquaint Softtech URL; pub_date: 2026-05-15; accessed 2026-09-23; confidence: medium (vendor composite, not a single-product retrospective); class: cost.

6. Per-tenant scraping isolates noisy-neighbor blast radius vs shared scraping; raises ops lifecycle cost. Source: https://nhimg.org/faq/what-is-the-difference-between-per-tenant-log-scraping-and-shared-log-scraping-i/ ; publisher: NHI Mgmt Group; pub_date: updated 2026-09-10; accessed 2026-09-23; confidence: medium (telemetry domain, analogous to scrape jobs); class: pattern.

7. Schema-per-tenant / DB-per-tenant migrations at hundreds of tenants require registry + per-tenant ledger + throttled waves; partial failure is a first-class failure mode. Source: https://itsnas.me/writing/migrating-schema-per-tenant-databases-at-scale ; publisher: Nas (@itsnas); pub_date: 2026-09-12; accessed 2026-09-23; confidence: high; class: implementation.

8. ARQ workers run as a separate process from FastAPI, isolating worker failure from the API process. Source: https://fastapi-patterns.com/async-background-tasks-observability/background-task-processing/running-arq-workers-with-fastapi/ ; publisher: FastAPI Patterns; pub_date: undated on fetch; accessed 2026-09-23; confidence: medium; class: implementation.

## Leads

- Citus “reference tables” docs (same mechanism as Azure tutorial) for undated official confirmation of shared-inventory joins.
- Ugur Aslim 2026-06-14 FastAPI multi-tenant background-task context incident — pair with an explicit Postgres naming source for a Q3 hit.
- Zero-Downtime Schema multi-tenant migration guide — confirm pub_date for Q4 strengthening.
- Eneo multi-tenant Scrapy/ARQ crawler (DeepWiki/repo) — per-tenant concurrency semaphores for scrape isolation; verify primary commit dates.
- savibm.com multi-tenant post (2026-03-12) — useful Model B cost narrative but **fails** screening freshness (before 2026-03-23); do not promote in later rounds without a fresher twin.

## Not found

- A single post–2026-03-23 source that jointly documents **FastAPI + PostgreSQL + background workers + multi-tenant** (Q3 → **not found**).
- A dated production cost study of **duplicated scrapes of the same public listing sites** at 5–10 tenants (only analogous per-tenant vs shared scraping evidence).
- A post–2026-03-23 production ops account showing schema-per-tenant **working smoothly** at tens-to-hundreds without migration tooling pain (Q4 evidence found only on the pain side).
- Exact marketplace wording “saved searches / favorites / alerts” overlay tables in a fresh primary source (inferred from shared `public` / reference + tenant-private schema pattern only).
