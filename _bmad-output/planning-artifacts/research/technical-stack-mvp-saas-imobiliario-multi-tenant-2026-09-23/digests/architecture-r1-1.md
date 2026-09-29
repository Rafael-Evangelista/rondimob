# Architecture patterns — round 1

Access date: 2026-09-23. Dimension: architecture patterns in practice (shared-corpus Model A + tenancy mechanisms). Stack preference is out of scope here; only pattern evidence.

## Findings

1. **Model A is expressible in Postgres RLS as table-scoped enablement.** Official Postgres 18 docs state that, by default, tables have no policies and all granted rows are equally available; RLS applies only after `ALTER TABLE … ENABLE ROW LEVEL SECURITY` on that table. Policies are table-specific. A shared public listings table can therefore stay without RLS (or with open SELECT policies), while radars/favorites/alerts/config tables enable (and force) RLS independently.

2. **Owner / superuser bypass is the documented failure mode unless FORCE is set.** Postgres: table owners normally bypass RLS; `ALTER TABLE … FORCE ROW LEVEL SECURITY` subjects the owner. Superusers and roles with `BYPASSRLS` always bypass. Implication for Model A app roles that own tables: ENABLE alone is insufficient isolation.

3. **Transaction-mode poolers make session `SET` unsafe for tenant GUCs.** Official PgBouncer feature map marks `SET/RESET` as **Never** compatible with transaction pooling—the mode that reassigns a server connection per transaction. Session-scoped tenant GUCs used by RLS can therefore outlive a request and bind to the next client on the same backend. Mitigations described in secondary sources (`SET LOCAL` / `set_config(..., true)` inside an explicit transaction) align with that official incompatibility; no dated postmortem after 2026-03-23 was retrieved this run.

4. **Framework/package recommendations diverge (and Django core has none).**
   - **Django:** Core docs do not prescribe SaaS tenancy. Maintainer package **django-tenants** implements **schema-per-tenant**, argues it is the ideal compromise, and explicitly supports **shared apps in `public`** (example: shared census-like data) alongside tenant-private schemas—structurally close to Model A’s shared corpus + private overlays.
   - **Laravel:** Maintainer package **stancl/tenancy** getting-started path is **multi-domain multi-database** (“what works best for the vast majority”); also documents single-DB scopes as supported elsewhere on the product site.
   - **Supabase/Postgres:** Official Supabase RLS guide treats **RLS as the isolation primitive** for exposed schemas (“table without RLS is readable/writable by any role with a grant”); policies are per-table SQL. Multi-tenant examples in Supabase testing docs use org membership + RLS, not schema-per-tenant.

5. **What breaks first (10 → few hundred tenants): only RLS-policy cost has concrete production numbers this run.** A retrospective (MonPG) reports a membership-subquery RLS policy on a shared-schema SaaS with ~40M invoice rows: dashboard p95 **9 ms → 1.4 s**, then **connection pool queuing** as queries held connections ~100× longer. Fix: simple `tenant_id = current_setting(...)` plus `FORCE ROW LEVEL SECURITY`. No retrieved source gave production numbers tying that growth band specifically to migration locks, raw connection-count-from-tenant-count, or noisy-neighbor scrapes.

## Claims

1. Tables without RLS (or with open policies) expose all privilege-granted rows; RLS is enabled per table via `ALTER TABLE … ENABLE ROW LEVEL SECURITY`; policies are table-specific.  
   URL: https://www.postgresql.org/docs/18/ddl-rowsecurity.html  
   Publisher: PostgreSQL Global Development Group  
   pub_date: undated (Postgres 18 manual; living doc)  
   accessed 2026-09-23  
   confidence: high  
   class: pattern

2. “Superusers and roles with the `BYPASSRLS` attribute always bypass the row security system when accessing a table. Table owners normally bypass row security as well, though a table owner can choose to be subject to row security with `ALTER TABLE ... FORCE ROW LEVEL SECURITY`.”  
   URL: https://www.postgresql.org/docs/18/ddl-rowsecurity.html  
   Publisher: PostgreSQL Global Development Group  
   pub_date: undated (Postgres 18 manual)  
   accessed 2026-09-23  
   confidence: high  
   class: implementation

3. PgBouncer transaction pooling: feature `SET/RESET` compatibility is **Never** (session pooling: Yes). Transaction pooling “breaks a few session-based features”; app must not rely on them.  
   URL: https://www.pgbouncer.org/features.html  
   Publisher: PgBouncer project  
   pub_date: undated (living official docs)  
   accessed 2026-09-23  
   confidence: high  
   class: pattern

4. django-tenants implements shared-DB / **schema-per-tenant**; documents three tenancy approaches and chooses schemas; supports **shared applications** in `public` (shared dataset readable by all tenants) plus tenant-specific apps.  
   URL: https://django-tenants.readthedocs.io/en/stable/index.html  
   Publisher: django-tenants (Read the Docs)  
   pub_date: undated  
   accessed 2026-09-23  
   confidence: medium  
   class: pattern  
   freshness: **low** (package docs undated)

5. Stancl Tenancy for Laravel getting-started demo is multi-domain **multi-database**; states that setup “works best for the vast majority of applications”; on TenantCreated, CreateDatabase + MigrateDatabase run per tenant.  
   URL: https://v4.tenancyforlaravel.com/getting-started/  
   Publisher: Tenancy for Laravel / Stancl  
   pub_date: undated (docs claim PHP 8.4 + Laravel 12 required)  
   accessed 2026-09-23  
   confidence: medium  
   class: pattern  
   freshness: **low** for undated page; version requirements are stated but not independently dated ≥ 2026-08-23

6. Supabase: “A table in an exposed schema without RLS is readable and writable by any role with a grant on it”; enable RLS then write per-operation policies; combine with Auth helpers such as `auth.uid()`.  
   URL: https://supabase.com/docs/guides/database/postgres/row-level-security  
   Publisher: Supabase  
   pub_date: undated (living docs)  
   accessed 2026-09-23  
   confidence: high  
   class: pattern

7. Production incident: membership-subquery RLS policy → p95 9 ms to 1.4 s on ~40M-row table; pool queued because sessions held ~100× longer; replaced with `tenant_id = current_setting('app.current_tenant')` and `FORCE ROW LEVEL SECURITY`; restored p95 under 15 ms. Secondary symptom was connection-pool pressure, root cause was **RLS policy plan shape**.  
   URL: https://monpg.app/blog/postgresql-row-level-security-performance  
   Publisher: MonPG  
   pub_date: undated (vendor engineering retrospective)  
   accessed 2026-09-23  
   confidence: medium  
   class: implementation  
   freshness: **low–medium** (no visible pub_date; not proven ≥ 2026-03-23)

8. django-tenants shared-app pattern: tables in `public` remain on the search path for every tenant (shared corpus pattern).  
   URL: https://django-tenants.readthedocs.io/en/stable/index.html  
   Publisher: django-tenants  
   pub_date: undated  
   accessed 2026-09-23  
   confidence: medium  
   class: pattern

## Leads

- Official Postgres `set_config(setting, value, is_local)` / `SET LOCAL` docs to harden claim that tenant GUCs must be transaction-local under poolers (complement PgBouncer “SET Never”).
- Supabase / Supavisor pooler docs for GUC + RLS under transaction mode (prefer over vendor blogs).
- Schema-per-tenant migration lock / connection-per-schema failure numbers at low hundreds of tenants (itsnas.me was blacklisted this round; need alternate primary).
- Dated postmortem (≥ 2026-03-23) of cross-tenant row visibility under PgBouncer/Supabase transaction pooling.
- Laravel core docs (if any) vs stancl-only guidance; django-rls / django-rls-tenants vs django-tenants for Model A RLS on shared schema.

## Not found

- Fresh (≥ 2026-03-23) **postmortem** of pooler GUC leak (only official PgBouncer incompatibility table + undated secondary guides).
- Django **core/official** recommendation among RLS / schema-per-tenant / tenant_id.
- Production numbers for this scale band proving **migration locks** or **noisy-neighbor scrapes** fail before RLS/pool effects.
- Evidence that **connection count alone** fails first when going from ~10 to a few hundred tenants under Model A (only secondary pool queuing after slow RLS).
- Version-dated (≥ 2026-08-23) confirmation of Laravel 12 / PHP 8.4 as current stancl requirement beyond the undated getting-started page.
