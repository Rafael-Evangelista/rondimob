# Adversary review — rondimob architecture spine

Checked: 2026-09-29. Target: `ARCHITECTURE-SPINE.md` (feature altitude). The spine was not edited.

Units one level down are the seed folders: `contas`, `anuncios`, `radares`, `coleta`. Each build below obeys AD-1 through AD-7 to the letter, and obeys the consistency table where that table speaks. Folder charters are granted as far as they go. The pairs still cannot share one database.

## Verdict

Fail. Six holes. Five are integration breaks; the sixth is the shared predicate vocabulary those breaks sit on. Closing each one is a new or tightened AD, not a story-level choice.

## Holes

### H1. Anúncio has two writers and two identities

**Clash:** two owners of one entity, plus the shared row shape.

**`coleta`:** The worker upserts the corpus inside the scrape task. AD-6 puts collection on the worker; the consistency table allows anúncio and price mutation only there; AD-1 is satisfied by a table with no `conta_id`. Natural key is `(fonte, url)`, because the spine never names an external id. Every successful scrape appends a `Preco` row (`numeric`, `timestamptz` UTC), including when the value did not change. Primary key is `bigint`. Anúncio is not on the UUID list.

**`anuncios`:** The same rules, the other charter. Capability map puts FR-7 on `anuncios` + worker, and the seed says this folder is the shared corpus and price history. The worker here upserts by a fingerprint of cidade + endereço + área + quartos + imobiliária, so two sources collapse to one row. A `Preco` row is inserted only when `numeric` changes. Primary key is UUID, by analogy with the other exposed ids.

**Why no current AD stops it:** AD-1 only forbids an account owner. AD-3 and AD-6 only place the write on the worker. The map gives that write to two folders. Nothing defines the natural key, whether unchanged scrapes append history, or which module owns the model. FR-7 in the PRD already prefers fonte + external id, else URL, and says a duplicate from the same run must not become a second anúncio. That rule never became an AD, so both keys are legal.

**Close with:** One owner. `anuncios` owns `Anúncio` and `Preço`; `coleta` submits a payload and does not declare those models. Identity is `(fonte, identificador externo)` when the source id is trustworthy, otherwise URL, unique in the single schema. State whether a scrape that repeats the current price appends a history row or only refreshes the collection timestamp. Favorito and any match row use that primary key, not a second exposed id.

### H2. “Seleciona” and “novo” have two mutation paths

**Clash:** conflicting state-mutation paths for the same membership.

**`radares`:** `Radar` stores the filter. There is no match table. The ER verb “seleciona” is a query. “Novo” is computed in the authenticated request: corpus rows that match and were not in this radar’s previous result set. Writing that set is not a mutation of `Radar`, `Favorito`, or `Alerta`, so the consistency table allows it in the web transaction. The worker never touches radar state. AD-6 is untouched because this query is not collection and not email.

**`coleta`:** On ingest, the worker writes `radar_anuncio (radar_id, anuncio_id, fato, visto_em)`. They treat it as corpus selection, not as a radar mutation, so the “only in the authenticated area” rule does not apply. AD-7 says collection does not spend a pesquisa, so this write is free and continuous. Dashboard and mail read the cache. No RLS: AD-1’s list is radar, favorito, alerta, and account configuration, not the through table.

**Why no current AD stops it:** The conventions split mutation by entity name and never name the relationship. A persisted match is either illegal for the worker (if it is radar state) or invisible to RLS (if it is not). A live query and a worker cache both satisfy every AD and disagree on whether a listing is new, whether it appears once, and whether the write waited for a logged-in execution.

**Close with:** Name the entity that records “this anúncio already surfaced for this radar” (first seen, and each price-drop fact). Give it one writer. Either the worker materializes it under a stated RLS policy and it is not a pesquisa, or only an authenticated execution writes it and the worker stops at the corpus. Say that the through table is account-private and listed with the FORCE RLS relations.

### H3. Cota and crédito: two clocks, two debits, two meanings of recarregar

**Clash:** conflicting mutations of one integer balance.

**`contas`:** Seed ownership is honored: this folder alone updates the integer saldo and the period counter. A pesquisa is a dedicated execute action. The counter resets on the plan anniversary in `America/Sao_Paulo`. Exhausted quota still allows GET of a stored snapshot. The last sentence of AD-7 (“pode recarregar”) is implemented as a free re-read of that snapshot. A pack purchase adds 10 in the web process, because AD-6 moves only collection and email out of the request.

**`radares`:** Running a radar against the corpus is the product action, so each dashboard run asks `contas` to decrement — including the daily open. The period they assume is the calendar month in UTC. “Pode recarregar” is a button that buys the pack and, on the same click, runs another search. They also accept a worker path that decrements when new matches appear, because that is “execução” and AD-7 only forbids charging the scrape itself.

**Why no current AD stops it:** AD-7 fixes the numbers, that collection is free, that credit is spent after quota, and that credit does not change the plan. It does not define the event that consumes one pesquisa, the timezone or boundary of “por mês” / “14 dias”, who is allowed to increment or decrement, or whether “recarregar” is a purchase or another execution. The PRD glossary (one execution of one radar; opening an existing result is free; recarregar is a credit pack) is not in the rule. Two callers of the same integer stay compliant.

**Close with:** Tighten AD-7. Only `contas` mutates cota and saldo. One pesquisa is one execution of one radar of that account against the corpus already stored; create/edit and opening a stored result do not debit; collection does not debit. State the period boundary and timezone. A pack grant is the only increment, and name the process that applies it (web request or worker — one of them). “Recarregar” means that grant, not a free rerun.

### H4. Alerta can be configured and still cannot record a send

**Clash:** two shapes for the same noun, and no legal write for delivery state.

**`radares`:** `Alerta` is email configuration on the account: new-listing on/off, price-drop on/off, frequency. Mutation stays in the authenticated transaction, under RLS. They add `ultimo_envio` on that row so a fact is not repeated. The worker is expected to update it after a send. There is no second message table, per the naming rule.

**`coleta`:** AD-6 means this process sends mail. It will not update `Alerta` (authenticated-area mutation only) and will not store per-account send flags on `Anúncio` (AD-1: the ad has no account). It creates `coleta.Envio (conta_id, anuncio_id, fato, janela)` and treats it as task state, not as Alerta. Dedup keys differ from `ultimo_envio`: one side dedupes per alert row, the other per (account, ad, fact, window).

**Why no current AD stops it:** The naming rule says Alerta is not a message table. The mutation rule then forbids the worker to write the only entity that exists. FR-10 still requires the same ad and the same fact at most once per chosen frequency. The two modules each invent the missing state in a different place. Both can cite an AD.

**Close with:** Split the nouns. `Alerta` stays configuration, owned by `radares`, written only in the authenticated transaction. Delivery is a separate ledger, owned by `coleta`, written only by the worker, under FORCE RLS, keyed so the same anúncio and the same fact enter once per frequency window. The worker updates the ledger, not `Alerta`.

### H5. Private tables, the GUC, and the worker role are not one policy

**Clash:** shared session shape and two owners of isolation.

**`contas`:** FORCE RLS on `radar`, `favorito`, `alerta`, and a `configuracao` table — the AD-1 list, read as closed. `Conta` and `Credito` are isolated with an ORM filter. The application role is not superuser and does not own those tables. Inside each transaction it runs `SELECT set_config('app.conta_id', ..., true)`. Policies compare `conta_id` to `current_setting('app.conta_id', true)`.

**`coleta`:** The worker must read every account’s alerts to send mail. AD-1’s “papel da aplicação” is read as the web role. The worker role is a different role with `BYPASSRLS` (not superuser, not required to be the table owner), so one query can see all alerts. It never sets `app.conta_id`. Separately, `radares` ships policies that read `current_setting('rls.conta_id')`.

**Why no current AD stops it:** AD-2 requires some account context inside the transaction and names neither the setting nor the role. AD-1 lists four relations and does not mention `Conta`, `Credito`, or a match/ledger table. FORCE RLS does not apply to a role with `BYPASSRLS`. One deployment therefore leaves account PII and balances on ORM filters, while the other bypasses RLS entirely for mail. Same ADs, different rows visible.

**Close with:** Name the setting (`app.conta_id` or whatever it is) and require every policy to use it. List every account-private relation, including `Conta` PII, `Credito`, the match rows from H2, and the delivery ledger from H4. One non-owner, non-superuser, non-`BYPASSRLS` role for web and worker. The worker’s cross-account pass is an explicit fan-out: read the account ids, then set the context per account inside a transaction. A second role, if it exists, does not bypass RLS.

### H6. Radar predicates and collected columns are different types

**Clash:** shared-data shape on the corpus fields a radar is allowed to compare.

**`coleta`:** Normalization emits the FR-6 minimum fields as text plus the one typed column the conventions demand (`preço numeric`). `tipo` is the source token (`apto`), `cidade` is the source string, `área` stays a string (`60m²`). AD-1–AD-7 do not constrain those columns.

**`radares`:** Filters are the FR-5 bounds: tipo from a fixed set, cidade from the four ABCD names, `área >= 60` as a number, `quartos` and `vagas` as integers. The query is equality and range on `anuncios` columns.

**Why no current AD stops it:** Conventions type price, credit balance, a few UUIDs, and the collection timestamp. They do not type area, counts, city, neighborhood, property type, or advertiser. Both modules are free to pick the “forma única” FR-6 asked for and still miss every row.

**Close with:** One column contract, owned by `anuncios`, written only through the worker upsert from H1. At least: `preço numeric`, `área numeric` in m², quartos/banheiros/vagas integers, and cidade, bairro, tipo, imobiliária anunciante as the same normalized text on both sides of the comparison. Radar filters may only reference that contract.

## What was tried and did not survive as a hole

- AD-4 (one schema, no django-tenants) does not fork. Both units stay in one schema.
- AD-5 (one app, same functions for CRECI and PJ) does not fork. Registration fields differ; the capability set does not.
- AD-3’s per-source queue is compatible as long as H1’s single upsert is the only write. Queue names can differ without two corpus shapes.
- Session lifetime is already one rule: until logout, and only that account.
