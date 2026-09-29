# Good-spine review — rondimob (architecture-rondimob-2026-09-23)

Reviewed: `ARCHITECTURE-SPINE.md` (feature altitude, draft, updated 2026-09-29).
Checklist: good-spine rubric. Spine text was not modified.
Brownfield: no application code in the repo. The spine matches the addendum (Django, PostgreSQL, Celery/Redis, worker process, one queue per source, shared listings, forced RLS, no django-tenants) and does not revive the FastAPI/Angular sketch in `MVP/mvp.md`.
Parent spine: none. Nothing to inherit or contradict.

## Verdict

Revise before epic handoff. The spine fixes the real tenant, process, and single-app seams, and the capability map names a home for FR-1 through FR-11. It still leaves epics free to disagree on listing identity, on what spends a pesquisa, and on how private credit is isolated. Operations and the payment provider are silent dimensions. The UI deferral is wide enough to split the client.

## Checklist

| Criterion | Result |
| --- | --- |
| Fixes real divergence points for the level below (epics), and misses none | Fail. Tenant, worker boundary, single app, and plan-shape are fixed. Listing identity, the debit event, credit RLS, the ABCD gate, personalizado, and the cross-source price contract are open. |
| Every AD Rule is enforceable and prevents its stated divergence | Partial. AD-3, AD-4, AD-5, AD-6, and AD-7 meet the divergence each one names. AD-1 meets the anúncio case and leaves crédito outside the RLS set. AD-2 describes the outcome and does not require a setting the server clears on abort. |
| Nothing under Deferred can let two units diverge | Fail. The UI-toolkit line can be read as an open rendering model. Host, source names, email vendor, and the parked product bets can wait. |
| Named tech versions look pinned | Partial. Django 6.1.1, PostgreSQL 18.6, Celery 5.6.3, and Redis 8.10.2 are exact. Python is a floating 3.13 micro. Currency against the web is out of this pass. |
| Covers the PRD capabilities it binds (FR-1 through FR-11) | Partial. The map has a row for each FR, including FR-11. Frontmatter `binds` stops at FR-10. FR-4, FR-5, and FR-7 are assigned ADs that do not carry the constraint those FRs actually turn on. |
| Every feature-altitude dimension is decided, deferred, or an open question | Fail. Environments are decided (local and one production; two processes; one PostgreSQL; one Redis). Host and region are deferred. Operations and the payment provider are named nowhere. |
| Brownfield ratification | Pass, against the addendum. |
| Inherited ADs | Not applicable. |

## Findings

### High

1. **Listing identity is not a rule** — Structural seed ERD; conventions; FR-7 row (governed only by AD-1 and AD-3).
   - **Disposition:** autofix.
   - **Trigger:** Coleta and the novo/preço epic can both obey AD-1 (anúncio has no account owner) and AD-3 (worker, per-source queue) and still dedupe on different keys.
   - **Consequence:** The same listing becomes two anúncios, or a new listing is swallowed. Price history cannot be reconstructed (FR-7).
   - **Fix:** Add an enforceable rule: identity is source plus external id; when that id is missing, identity is the URL. A duplicate in the same collect does not insert a second anúncio. Only the worker appends price history, as the convention already says.

2. **AD-7 restates quotas and leaves the debit event and the blocked surface unspecified** — AD-7 (lines 83–87); FR-4 and FR-11 rows.
   - **Disposition:** autofix.
   - **Trigger:** The rule fixes equal functions across paid plans, the numeric quotas, credit-after-quota, and “coleta does not spend.” It never says what one pesquisa is, which process runs it, or which module decrements saldo. The no-plan sentence blocks executing a pesquisa and is silent on favoritar and configurar alerta, which FR-4 blocks.
   - **Consequence:** The radar epic debits on save; the contas epic debits on execute. Radares keeps favorite and alert edits available with no plan, because that still complies with AD-7. Builders who treat AD-7 as the full FR-4 contract override the PRD.
   - **Fix:** State the PRD unit in the rule: one pesquisa is one execution of one radar against the corpus already collected; creating or editing a radar does not spend; opening a result already generated does not spend again. Name the single writer of saldo (contas, inside the account transaction). Without a plan, the account sees radar names and plans, and does not execute a pesquisa, favorite, or change alerta. With quota exhausted, it sees results already generated and can buy credit.

3. **FORCE RLS does not cover crédito** — AD-1 (lines 47–51); ERD `CONTA ||--o{ CREDITO`.
   - **Disposition:** autofix.
   - **Trigger:** The rule lists radar, favorito, alerta, and “configuração da conta.” Crédito is its own entity. Plano state has no named table. “Configuração da conta” is not a seed folder or an ERD entity, so a builder can treat saldo as an ORM filter on a table the app role owns.
   - **Consequence:** One epic isolates listings and radars with forced RLS and another isolates balance with a queryset. That is the divergence AD-1 exists to stop, applied to the commercial data.
   - **Fix:** Name the private relations that require `ENABLE` and `FORCE ROW LEVEL SECURITY`, including crédito and plan/quota state. Keep anúncio free of an account owner.

4. **Operations is a silent dimension** — absent from Design Paradigm, Structural Seed, Stack, Deferred, and every AD. AD-3 only says a source error “fica registrado,” with no sink.
   - **Disposition:** defer. Record an open question; do not invent a host or a vendor.
   - **Trigger:** Feature altitude owns the operational envelope. Environments and process topology are decided. Host and region are deferred. Nothing decides or defers how the two processes are supervised, how schema migrations are applied, how PostgreSQL is backed up, or where coleta failures and request logs go.
   - **Consequence:** The web epic and the worker epic ship different log sinks and different migrate/run stories. Production is undeployable as one system even after a host is chosen.
   - **Fix:** Add a Deferred or open-question line that lists those four operational choices as explicitly unbound, so a later epic cannot fill them independently.

5. **Payment provider is a silent provider decision** — FR-11 row; AD-7 describes the pack and the balance effect only. Email vendor is deferred; this one is not.
   - **Disposition:** defer. Name it as an open provider choice.
   - **Trigger:** “Compra” and “recarregar” are in the product. No AD, convention, or Deferred line says whether credit is granted by a card/Pix webhook, by a manual mark, or by something else.
   - **Consequence:** Contas and a billing epic both obey AD-7 (credit lands on the account, plan unchanged) and integrate different rails.
   - **Fix:** Defer the provider in one line, and pin the architectural outcome that is already decided: only contas grants saldo, and only after the chosen provider confirms payment.

### Medium

6. **AD-2 can be satisfied by a session `SET` that leaks on abort** — AD-2 (lines 53–57).
   - **Disposition:** autofix.
   - **Trigger:** The rule requires the account context to be set inside the transaction and to end with it. A success-path `SET` plus manual reset meets that wording. The Prevents clause is the pooler leak, which happens when the connection returns to the pool after an error before the reset runs.
   - **Consequence:** Two requests on one pooled connection see two accounts. Forced RLS then enforces the wrong context.
   - **Fix:** Require a transaction-scoped setting the server clears on commit and on abort (`SET LOCAL` or `set_config(..., true)`), issued before private queries.

7. **Deferred UI toolkit can split the client** — Deferred, first bullet; FR-1 row says “templates do app web”; Stack has no frontend framework.
   - **Disposition:** discuss.
   - **Trigger:** Palette can wait. “Biblioteca de interface ficou aberta” can also be read as permission to introduce a second client (SPA or separate asset pipeline) beside Django.
   - **Consequence:** One epic renders the portal as Django templates; another adds a frontend app and a JSON API the spine never bounded.
   - **Fix:** Pin the surface as server-rendered templates in the same Django app. Defer palette and the component library inside that surface.

8. **Personalizado is a fourth plan the spine never mentions** — AD-7; FR-1 requires grátis, padrão, plus, and personalizado.
   - **Disposition:** autofix.
   - **Trigger:** AD-7 enumerates grátis, padrão, plus, and the credit pack. A billing epic can ship three SKUs. The portal epic must show a contact plan with no self-serve quota.
   - **Consequence:** The public pricing page and the account plan model disagree.
   - **Fix:** State that personalizado is contact-only in this version: no self-serve price, no extra functions, and it does not change the quota rules of padrão and plus.

9. **FR-5 is governed by isolation rules and not by the ABCD gate** — map row FR-5 (AD-1, AD-2). The spine never says ABCD.
   - **Disposition:** autofix.
   - **Trigger:** The radar epic can accept any city and still force RLS. The PRD rejects radar creation outside Santo André, São Bernardo do Campo, São Caetano do Sul, and Diadema.
   - **Consequence:** Radars and the corpus filters diverge by city.
   - **Fix:** One sentence on the radar rule: a radar is stored only when the city is one of those four.

10. **“Preço é numeric” does not fix scale or parse across fontes** — conventions, Data & formats; AD-3 invites one unit per source.
    - **Disposition:** autofix.
    - **Trigger:** Each source queue can parse “R$ 650.000”, “650 mil”, and “650000” into a different numeric (reais versus centavos, or a rejected row). All of them store `numeric`.
    - **Consequence:** History and comparison across sources are wrong while every AD still holds.
    - **Fix:** Pin the unit (reais, `numeric`) and require one normalizer in `anuncios` that every coleta task calls before insert.

11. **Alerta cadence lives in two modules with no shared shape** — naming convention; FR-10 row (coleta, worker, AD-6); alerta is configured under radares.
    - **Disposition:** autofix.
    - **Trigger:** AD-6 puts send on the worker. The naming line stops a second message table. Frequency (imediata, diária, semanal; default diária) and once-per-anúncio-per-fact-per-period live only in the PRD.
    - **Consequence:** Radares stores a free-text cadence; coleta sends a daily digest and repeats the same price drop.
    - **Fix:** Put those two constraints in the convention next to the alerta definition.

12. **Python is not pinned the way the rest of the stack is** — Stack row “Python | 3.13, micro mais recente”.
    - **Disposition:** discuss.
    - **Trigger:** The other four rows are exact versions. This row floats the patch. The memlog records that float on purpose (3.13 is the overlap of Django 6.1 and Celery 5.6; 3.14 stays out).
    - **Consequence:** Local and production can run different 3.13 micros. That is milder than an empty version cell, and it still fails a pin reading.
    - **Fix:** Either pin the micro that was current when the row was written, or state in the Stack note that the pin is 3.13 and the patch float is the policy.

### Low

13. **Frontmatter `binds` omits FR-11** — lines 11–21 versus the FR-11 map row and AD-7.
    - **Disposition:** autofix.
    - **Trigger:** The body governs credits. The header list a downstream auditor trusts stops at FR-10.
    - **Consequence:** A coverage check that reads only `binds` drops recarga.
    - **Fix:** Add FR-11 to `binds`.

14. **The data-formats convention never sets an error shape** — conventions row that names error shapes and envelopes, then specifies only numeric, UUID, timestamptz, and integer balance.
    - **Disposition:** defer, together with the UI surface.
    - **Trigger:** Two epics invent different form and API error bodies. With server templates pinned, HTML form errors may be enough and a JSON envelope may be unnecessary.
    - **Consequence:** Small, until a second client appears (finding 7).
    - **Fix:** After the template surface is pinned, either name the error convention or defer it in one line.

## What holds

- AD-3 is enforceable: separate worker process, one queue per source, one source’s failure does not cancel the others or the site.
- AD-4 is enforceable: one schema, django-tenants out of this version.
- AD-5 is enforceable: one app, one client area, corretor CRECI and imobiliária PJ get the same functions, registration is what changes.
- AD-6 matches its Prevents clause: coleta and email send are worker tasks, so they stay out of the HTTP request. Password recovery goes through that same rule.
- AD-7 does prevent the divergence it names: paid plans do not grow features in order to sell more pesquisas, and shared coleta is not debited from the account.
- Session convention matches FR-2: the session lasts until logout and only for that account.
- Seed folder limits (`config`, `contas`, `anuncios`, `radares`, `coleta`) give each epic a boundary.
- Dependency sketch matches the paradigm: the web app reaches PostgreSQL and Redis; the worker reaches Redis, PostgreSQL, and the sources; the web app does not scrape inside the diagram.
- Deferred items that can wait: host and region (topology is already fixed), the names of the first two or three sources (PRD says the architecture does not depend on which site), the email vendor (one sender, the worker), and RAG, fine tuning, WhatsApp, score, and a mobile app (out of this version).
- Stack rows other than Python look pinned. No parent AD is weakened. No placeholder markers.

## Mechanical notes

- AD-1 through AD-7 ascend, no reused ids, each with Binds, Prevents, and Rule, each tagged ADOPTED.
- No `TBD` / `TODO` / unresolved “similar to AD-n”.
- Capability map includes FR-11; frontmatter `binds` does not (finding 13).
- Glossary prices in the PRD still say the real amount is open; FR-1, section 8, and the 2026-09-29 decisions close them. AD-7 follows the closed numbers. That is consistent with the later PRD text.
- This pass did not re-check version currency on the web. The memlog cites Django 6.1.1, PostgreSQL 18.6, Celery 5.6.3, and Redis 8.10.2 as looked up on 2026-09-23 (Redis note updated from endoflife.date).
