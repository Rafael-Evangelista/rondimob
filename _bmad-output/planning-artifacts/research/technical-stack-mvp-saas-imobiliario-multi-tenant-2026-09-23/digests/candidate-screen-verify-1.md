# Candidate screen — spot-check

Access date: 2026-09-23. Fresh-context check of three load-bearing claims, plus one lead follow for the cost URL.

## Results

1. Microsoft Learn multi-tenant Postgres tutorial — mechanism verified. The cluster stores a synchronized copy of a reference table on every worker node, while tenant tables are distributed by a tenant key. The spot-check fetch did not show `ms.date`; publication date stays unknown. URL: https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/tutorial-multitenant-database

2. Acquaint Softtech (2026-05-15) — page confirms ~50 tenants: database-per-tenant $2,000–$4,500/mo and 4–8 hrs/wk DevOps vs shared schema $400–$900/mo. URL: https://acquaintsoft.com/blog/multi-tenant-saas-architecture-guide

3. Independent order-of-magnitude check — MarsDevs, pricing validated April 2026: dedicated managed Postgres baseline $40–$120 per tenant per month before compute, sourced from provider pricing pages. At 50 tenants that is about $2,000–$6,000/mo, same direction and order as claim 2. Both publishers are vendors. Both dates are older than the 3-month pricing bar (cutoff 2026-06-23). URL: https://www.marsdevs.com/compare/multi-tenant-vs-single-tenant-saas

4. ADHDecode (2026-04-16) — verified: FastAPI sets `search_path` to the tenant schema then `public` for shared tables. Workers are not mentioned. URL: https://adhdecode.com/articles/fastapi/fastapi-multi-tenancy-implementation/
