# Candidate screen — round 1

Access date: 2026-09-23. Freshness gate for screening claims: published on or after 2026-03-23. Version/compatibility claims require sources on or after 2026-08-23 (none in this run met that bar with hard version numbers; version-class claims below are marked low).

Epistemic note: Project context was used only to shape queries. Conclusions below are limited to evidence retrieved this run. Explicit mapping of tenancy patterns to data models **(A) shared listing corpus + tenant-private radars/favorites/alerts** vs **(B) per-brokerage database and collection** was **not found** in fresh sources; pattern→A/B cells state only what sources support, else “not evidenced.”

---

## Finalists

### Stack finalists (5)

1. **Next.js + Supabase (Postgres + Auth + RLS) + managed background jobs (Trigger.dev / Inngest) + Stripe + Vercel (or Railway/self-host fallback)**  
   - **Gates:** Solo/small-team SaaS shipping path and coherent auth+Postgres+RLS bundle (Makerkit 2026-05-08); modular monolith / avoid day-one microservices; Postgres+RLS as default multi-tenant start up to ~10K tenants (Agile Soft Labs 2026-03-30); pre-launch infra ~$1/mo and ~$92–115/mo excl. Stripe at $1K MRR (Makerkit) — compatible with 5–10 brokerage validation scale. Job offload recommended vs DIY cron (Makerkit).  
   - **Data models:** Serves shared-schema multi-tenant apps with `tenant_id` + RLS (Makerkit; Agile Soft Labs). **Model A/B:** not evidenced for listing-corpus shapes.

2. **Django + PostgreSQL + Celery + Redis (+ Docker multi-process: web / worker / beat)**  
   - **Gates:** Celery+Redis framed as 2026 production standard for Django off-request work (emails, scheduled jobs, syncs) with **queue separation** so bulk work does not block critical queues (Softaims 2026-04-02) — supports gate 3 at the *job-queue* layer if scraper/sync work is isolated onto bulk workers. Batteries-included SaaS path acknowledged as productive alternative to JS stack (Makerkit 2026-05-08 “Why Not Rails or Django or Laravel?”). Solo MVP scope: auth, admin, ORM, scheduled tasks — consistent with Softaims + Makerkit framing; no contradictory cut found this run.  
   - **Data models:** Compatible with Postgres shared-schema RLS patterns documented generally (PostgreSQL docs; ClickHouse 2026-05-25). **Model A/B:** not evidenced for listing-corpus shapes. Schema-per-tenant appears in older advocacy outside the freshness window — not used as pass evidence here.

3. **Laravel + PostgreSQL + Redis (cache/queues) + React (or Inertia) + worker processes**  
   - **Gates:** Author reports production Laravel SaaS (200+ restaurant outlets multi-tenant; learning platform 50,000 concurrent users) and argues shared-`tenant_id` start with optional later dedicated DB for demanding customers (Khawar Hussain 2026-06-19, updated 2026-08-03). Tenancy, billing, Redis queues, and day-one HA shape called out as reversible-cost decisions. Solo-shippable for CRUD/SaaS-shaped products per that retrospective. Operating cost path: start shared tables (lowest ops) before DB-per-tenant.  
   - **Data models:** Shared tables + `tenant_id` default; database-per-tenant as later isolation upgrade (Khawar). **Model A/B:** not evidenced for listing-corpus shapes.

4. **Node.js + NestJS (or Express) + PostgreSQL + Redis (scale path)**  
   - **Gates:** Listed as backend option for high-growth / rapid prototyping SaaS alongside Django and serverless in Agile Soft Labs 2026-03-30 recommendations-by-scale table/FAQ; Postgres+RLS still the data default in the same article. Passes solo MVP only if the implementer already knows Nest/TS — article does not claim Nest is the fastest solo path vs Next.js full-stack. Credible **challenger** in the 2026 field, not the primary leader.  
   - **Data models:** Same Postgres tenancy options as other API stacks (Agile Soft Labs; ClickHouse). **Model A/B:** not evidenced.

5. **Wildcard: Rails 8–era “boring stack” (Hotwire + Postgres + Solid Queue / similar) when the solo builder is already fluent in Rails**  
   - **Gates:** Makerkit 2026-05-08 explicitly: if the team knows Rails cold and the product is CRUD-shaped SaaS, ship Rails — language-hire and AI-codegen arguments favor TS for *their* kits, not a hard technical fail of Rails. Passes solo-ship and cost gates as a skill-matched alternative. Fresh **production-number** Rails retrospectives were thin this run (mostly starter-kit marketing).  
   - **Data models:** Not mapped to A/B this run. Row-level tenancy appears in undated starter READMEs — **not** used as evidence.

### Tenancy-pattern finalists (3)

1. **Shared schema + `tenant_id` + PostgreSQL Row-Level Security (RLS)**  
   - **Gates:** Lowest operational overhead; ClickHouse 2026-05-25 calls shared schema + `tenant_id` the right default for most new B2B SaaS in 2026; Agile Soft Labs 2026-03-30: RLS start, works well up to ~10K tenants — covers validation (5–10) and path to low hundreds. Isolation from day one via DB policies + app middleware. Growth without tenancy rewrite: same article + ClickHouse scaling ladder (replicas → partition → dedicated whales). Cost: lowest infra density (ClickHouse compare table).  
   - **Data models:** Strong fit for **tenant-private** rows. **Model A (shared corpus):** not evidenced — sources assume `tenant_id` on tenant tables; shared public listing tables with different policies are a plausible Postgres capability (official RLS docs) but **not** product-pattern-evidenced this run. **Model B:** not the pattern’s intent.

2. **Database-per-tenant (dedicated Postgres database/cluster per brokerage)**  
   - **Gates:** Strongest physical blast-radius and compliance boundaries; zero storage-layer noisy neighbor (ClickHouse 2026-05-25; Agile Soft Labs; Khawar). Supports gate 3 strongly for DB-side failure isolation. Gate 5: highest cost / idle waste — acceptable only selectively at 5–10 tenants if automation exists; ClickHouse stresses fully automated provisioning. Gate 4: Khawar regrets starting here then collapsing back; better as upgrade path.  
   - **Data models:** Natural fit for **Model B** (per-brokerage DB). **Model A:** ClickHouse notes analytics fan-in from many tenant DBs — implies shared corpus is *harder*, not that A is supported as a first-class pattern.

3. **Hybrid tiering (shared schema for standard tenants; dedicated DB for enterprise/whales)**  
   - **Gates:** ClickHouse 2026-05-25 “mature scale-up shape”; Agile Soft Labs hybrid column; Khawar: start shared, move one demanding customer to dedicated DB later. Passes growth-without-rewrite if routing table / dual pipeline is planned. Ops complexity high — finalist as *path*, not day-one default for a solo MVP.  
   - **Data models:** Can evolve toward **B** for select brokerages while majority stay shared. **Model A:** not evidenced.

---

## Cuts

| Name | Why cut / not top field | Source |
| --- | --- | --- |
| **Angular as primary dashboard UI** | Explicitly rejected in 2026 SaaS stack pick vs React: “heavier, smaller hiring pool.” Fails competitive solo-field vs Next/React for this decision. | Makerkit, 2026-05-08 |
| **FastAPI-only as the full SaaS application stack** | Fresh (≤6mo) production retrospectives tying FastAPI alone to auth + multi-tenant admin + billing + dashboard were **not found** this run. Django/Laravel/Next framed as batteries-included; FastAPI positioned elsewhere as API/AI layer. Starting hypothesis remains unverified as a full-stack finalist. | Softaims 2026-04-02 (Django+Celery, not FastAPI); Makerkit 2026-05-08; search landscape thin |
| **Plain DIY cron as long-term job system** | Makerkit: DIY cron “works until it doesn't”; Softaims: Beat + queue isolation for production scheduled/background work. Weak for scheduled scrapers + email at SaaS shape. | Makerkit 2026-05-08; Softaims 2026-04-02 |
| **Schema-per-tenant as the default day-one pattern** | ClickHouse 2026-05-25: “rarely the right pick,” migration/catalog bloat trap at scale. Agile Soft Labs positions it for ~50–500 tenants with heavy customization — outside “default for validation” and conflicts with ClickHouse default. Cut from **default** finalists; not discarded forever for niche isolation. | ClickHouse 2026-05-25; Agile Soft Labs 2026-03-30 |
| **Database-per-tenant as the default for all brokerages from day one** | Highest cost, linear ops (ClickHouse; Agile Soft Labs; Khawar). Fails gate 5 as *universal* default at validation scale; kept only as pattern finalist #2 / hybrid upgrade. | ClickHouse 2026-05-25; Khawar 2026-06-19 |
| **Microservices / CQRS / event sourcing for MVP** | Agile Soft Labs: over-engineering; modular monolith first. | Agile Soft Labs 2026-03-30 |
| **Clerk + separate Supabase Auth + app profiles “Frankenstein” auth** | Makerkit anti-pattern: multiple user sources of truth. | Makerkit 2026-05-08 |
| **MongoDB as primary OLTP for this domain** | Postgres recommended default for ~95% SaaS incl. RLS (Agile Soft Labs). | Agile Soft Labs 2026-03-30 |
| **Rails/Angular Heroku starter kits / undated SaaS boilerplates** | Marketing or undated; no fresh production numbers meeting source-quality bar. | Search hits (e.g. market.dev starter, Ignite Rails) — not fetched as primary evidence |
| **DEV Community Django MVP post (2026-03-11)** | Would support Django+schema-per-tenant+Celery, but **pub_date before freshness gate (2026-03-23)** — inadmissible for screening conclusions. | Kirill Strelnikov / DEV, 2026-03-11 |

---

## Claims

| claim | source URL | publisher | pub_date | accessed | confidence | class |
| --- | --- | --- | --- | --- | --- | --- |
| Recommended 2026 production SaaS stack: Next.js 16 + React 19 + Supabase (Postgres) + Drizzle + Better Auth or Supabase Auth + Stripe + Tailwind 4 + Shadcn + Turborepo on Vercel; solo/small teams called out as audience | https://makerkit.dev/blog/saas/saas-stack-2026 | Makerkit | 2026-05-08 | 2026-09-23 | medium (vendor kit advocacy + claimed customer deployments; not third-party audit) | landscape |
| Angular rejected vs React for SaaS UI: heavier, smaller hiring pool | https://makerkit.dev/blog/saas/saas-stack-2026 | Makerkit | 2026-05-08 | 2026-09-23 | medium | landscape |
| Background jobs: Trigger.dev or Inngest preferred over DIY cron | https://makerkit.dev/blog/saas/saas-stack-2026 | Makerkit | 2026-05-08 | 2026-09-23 | medium | implementation |
| Stack cost excl. Stripe fees: ~$1/mo pre-launch; ~$92–115/mo at $1K MRR; ~$306–960/mo at $10K MRR (their modeled services) | https://makerkit.dev/blog/saas/saas-stack-2026 | Makerkit | 2026-05-08 | 2026-09-23 | medium (self-reported MakerKit/customer reports) | cost |
| Rails/Django/Laravel remain productive; Makerkit still prefers TS for one-language hiring and AI codegen — but advises shipping Rails if the team knows it cold | https://makerkit.dev/blog/saas/saas-stack-2026 | Makerkit | 2026-05-08 | 2026-09-23 | medium | landscape |
| Clerk+Supabase+app profiles multi-source user sync is a costly anti-pattern | https://makerkit.dev/blog/saas/saas-stack-2026 | Makerkit | 2026-05-08 | 2026-09-23 | medium | implementation |
| Start multi-tenant with `tenant_id` + Postgres RLS; shared schema works well to ~10K tenants; schema-per-tenant for ~50–500 with customization; DB-per-tenant for enterprise/regulated | https://www.agilesoftlabs.com/blog/2026/03/best-saas-tech-stack-architecture-2026 | Agile Soft Labs | 2026-03-30 | 2026-09-23 | medium (consultancy guide; some market stats unsourced) | pattern |
| Prefer Next.js for SaaS dashboards; PostgreSQL default for ~95% SaaS; modular monolith over microservices for MVP; read replicas before CQRS | https://www.agilesoftlabs.com/blog/2026/03/best-saas-tech-stack-architecture-2026 | Agile Soft Labs | 2026-03-30 | 2026-09-23 | medium | landscape |
| Backend options named include Node/NestJS, Django, Go, serverless — Node claimed to power “70% new SaaS startups” (stat not independently verified this run) | https://www.agilesoftlabs.com/blog/2026/03/best-saas-tech-stack-architecture-2026 | Agile Soft Labs | 2026-03-30 | 2026-09-23 | low (FAQ-style claim) | landscape |
| Shared schema + `tenant_id` is the right default for most new B2B SaaS in 2026; schema-per-tenant rarely worth it; DB-per-tenant for regulated/white-label; hybrid tiering is mature scale-up | https://clickhouse.com/resources/engineering/multi-tenant-saas-postgres-architecture | ClickHouse (Manveer Chawla) | 2026-05-25 (last updated) | 2026-09-23 | medium-high (engineering depth; vendor has OLAP product interest) | pattern |
| Notion cited as shared-schema pattern at large shard count (480 logical shards / 32 physical DBs) | https://clickhouse.com/resources/engineering/multi-tenant-saas-postgres-architecture | ClickHouse | 2026-05-25 | 2026-09-23 | medium (secondary citation inside article; upstream Notion post not re-fetched) | pattern |
| Tenant context must be transaction-scoped (`set_config(..., true)`) under transaction-mode poolers to avoid cross-tenant leakage | https://clickhouse.com/resources/engineering/multi-tenant-saas-postgres-architecture | ClickHouse | 2026-05-25 | 2026-09-23 | high (aligns with known pooler semantics; primary engineering argument) | implementation |
| Background jobs must carry `tenant_id`, set tenant config before work, and avoid global bypass paths; pin heavy jobs to dedicated compute to limit noisy neighbors | https://clickhouse.com/resources/engineering/multi-tenant-saas-postgres-architecture | ClickHouse | 2026-05-25 | 2026-09-23 | high | implementation |
| Postgres RLS can restrict which rows are visible/modifiable per policy; owners/superusers bypass unless FORCE; default-deny when enabled with no policy | https://www.postgresql.org/docs/current/ddl-rowsecurity.html | PostgreSQL Global Development Group | unknown (docs for PostgreSQL 18 “current”) | 2026-09-23 | high for mechanism; **low for freshness date** (page undated) | pattern |
| Celery + Redis remains a 2026 production standard for Django background/scheduled tasks; separate queues/workers by priority so bulk jobs do not block critical work | https://softaims.com/blog/django-celery-background-tasks-production-2026 | Softaims | 2026-04-02 (updated 2026-04-08) | 2026-09-23 | medium (vendor blog; patterns are concrete) | implementation |
| Author has run multi-tenant Laravel SaaS (200+ restaurant outlets) and a learning platform at 50,000 concurrent users; prefers start shared `tenant_id`, move demanding customer to dedicated DB later; reverse is costly | https://khawarr.com/blog/laravel-saas-architecture-guide | Khawar Hussain | 2026-06-19 (updated 2026-08-03) | 2026-09-23 | medium-high (first-person production numbers; single-author) | landscape |
| Shared vs schema-per vs DB-per tradeoffs: isolation mechanism, migration cost, noisy neighbors, restore difficulty (table) | https://khawarr.com/blog/laravel-saas-architecture-guide | Khawar Hussain | 2026-06-19 | 2026-09-23 | medium-high | pattern |
| Day-one deploy shape includes Redis for cache/queues; dedicated queue workers can wait until jobs contend with web traffic | https://khawarr.com/blog/laravel-saas-architecture-guide | Khawar Hussain | 2026-06-19 | 2026-09-23 | medium | implementation |
| Unverified belief (not evidenced this run): BeautifulSoup/Playwright + FastAPI + Angular + cron→Celery is an optimal solo MVP→SaaS path | — | — | — | 2026-09-23 | n/a — hypothesis only | landscape |

---

## Leads

1. **Model A vs B head-to-head:** No fresh primary source discussed a *shared listing corpus* with tenant-private radars/alerts. Round 2 should search engineering posts on marketplace/aggregator multi-tenancy, “shared catalog + tenant overlays,” or real-estate proptech architectures.  
2. **Contradiction to resolve:** ClickHouse (2026-05) calls schema-per-tenant a trap; Agile Soft Labs (2026-03) still recommends it for 50–500 tenants with customization; a pre-gate Django post (2026-03-11, inadmissible) uses `django-tenants` schema-per-tenant. Need production migration/ops numbers.  
3. **Scraper blast radius:** Evidence covers *queue* and *DB* isolation, not “one source’s scraper failure” across accounts. Round 2: process sandboxing, per-source workers, circuit breakers, Playwright pool isolation.  
4. **FastAPI hybrid:** Landscape snippets suggest Django/Laravel/Next core + FastAPI sidecar; no qualifying fresh fetch committed — verify if still current.  
5. **Version freeze:** No source on/after 2026-08-23 pinned exact framework minors for Next 16 / Django 5 / Postgres 18 compatibility — round 2 should fetch official release notes within the 1-month window.  
6. **NestJS vs Next full-stack:** Nest appears only as a named option; need a dated Nest multi-tenant production retrospective.  
7. **Wildcard depth:** Rails 8 Solid Queue / Kamal production ops at low-hundreds tenants.

---

## Not found

- Fresh (on/after 2026-03-23) **production** accounts of **FastAPI-only** multi-tenant SaaS covering auth, dashboard, email, and scraping pipelines.  
- Any source explicitly comparing **Model A (shared listing corpus)** vs **Model B (per-brokerage collection/DB)** for real-estate monitors.  
- Fresh **Angular**-first SaaS production retrospective arguing Angular over React for solo B2B dashboards (only a rejection found).  
- Dated **Playwright/BeautifulSoup** scraping-at-SaaS-scale ops post inside the freshness window (not searched exhaustively; no hit rose to fetch budget).  
- Official **Supabase RLS multi-tenant** guide fetch this run (Supabase named via Makerkit/Agile Soft Labs only).  
- **PostgreSQL.org** page publish date (mechanism documented; freshness unmarked).  
- Sources on/after **2026-08-23** for hard **version/compatibility** claims.  
- Independent verification of Agile Soft Labs “70% new SaaS on Node” statistic.  
- Cost model specific to **5–10 brokerages / thousands of listings / scraper compute** (Makerkit costs are generic SaaS hosting, not scrape-heavy workloads).

---

## Sources actually fetched/read this run (8)

1. https://makerkit.dev/blog/saas/saas-stack-2026 — 2026-05-08  
2. https://www.agilesoftlabs.com/blog/2026/03/best-saas-tech-stack-architecture-2026 — 2026-03-30  
3. https://clickhouse.com/resources/engineering/multi-tenant-saas-postgres-architecture — 2026-05-25  
4. https://www.postgresql.org/docs/current/ddl-rowsecurity.html — date unknown  
5. https://khawarr.com/blog/laravel-saas-architecture-guide — 2026-06-19 / updated 2026-08-03  
6. https://softaims.com/blog/django-celery-background-tasks-production-2026 — 2026-04-02  
7. https://dev.to/kirill_strelnikov_d8546b8/the-django-saas-mvp-stack-i-use-in-2026-ships-in-4-6-weeks-bnc — 2026-03-11 (**read; excluded from screening conclusions — pre-freshness gate**)  
8. Partial auto-dumps consulted from search for the above; Laravel MVP (khaledahmed) and IT Path Solutions pages appeared in search dumps but were **not** used as dated screening evidence (pub_date unclear / quality lower).

Tool budget: WebSearch/WebFetch calls used within the 15-call cap; stop for round 1.
