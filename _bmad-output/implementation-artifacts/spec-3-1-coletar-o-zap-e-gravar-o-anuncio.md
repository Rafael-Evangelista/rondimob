---
title: 'Coletar o ZAP e gravar o anúncio'
type: 'feature'
created: '2026-09-30'
status: 'done'
route: 'dispatch'
baseline_commit: '94015df0c65aeaf239ef19de8a5e71f7817f955e'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing stores a ZAP listing. A later search would have to open the site at request time.

**Approach:** A Celery task on the ZAP queue reads a recorded payload and upserts it into the shared corpus. The web request does not collect. Tests never call ZAP.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1, Celery 5.6.3, broker `redis://localhost:6379/0`. `coleta.tasks.coletar_zap` is routed to the queue `zap` and is not called from a view. `anuncios` owns `Anuncio` and `Preco`. `coleta` parses the payload and records a failure; it does not declare those models. Price and area are `numeric`, area in m². Quartos, banheiros and vagas are integers. Cidade, bairro, tipo and imobiliária are trimmed and casefolded. `coletado_em` is timezone-aware UTC. "R$ 650.000", "650 mil" and "650000" are the same numeric 650000. The unique key is fonte `zap` plus `identificador_externo` when that id is present; otherwise fonte plus URL. The same price updates `coletado_em` only. A different numeric price adds one `Preco` row and updates the listing. The corpus has no account owner and no RLS. Grants let `rondimob_worker` insert. Those grants depend on `contas.0002`, which creates the role. A failure is a `coleta` row plus one stdout line. No account counter changes and `RadarVisto` is not written. The payload in tests is the fixture file, not a network response.

**Never:** Do not call ZAP, Viva Real, OLX, or any other site. Do not add credentials, tokens, or a live client. Do not implement stories 3.2 through 3.5, and do not spend quota or write `RadarVisto`. Do not put RLS on the corpus. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts. Do not delete the existing `deferred-work.md` entry. Do not mark `epic-3-retrospective` done.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Recorded payload | Fixture with id, URL, "R$ 650.000", area 60, rooms, baths, spaces, city, agency | One listing and one price row. Text is casefolded. `coletado_em` is UTC. No HTTP view created it. | A payload without URL writes a failure and no listing. |
| Same price | "650 mil", then "650000", same external id | Still one listing and one price row. `coletado_em` moves to the second run. | N/A |
| New price | Same id, price "700000" | The listing price is 700000. Two price rows exist. | N/A |
| No external id | Payload with URL and no id | The URL is the key. A second payload with that URL does not create another listing. | N/A |
| Quota | An account exists. The task runs | Free, month, and credit counters stay unchanged. No `RadarVisto` model is written. | A raised parser error is stored as a failure and printed to stdout. |
| SQLite | `uv run pytest` | Upsert tests pass without Redis and without the network. | N/A |

</frozen-after-approval>

## Code Map

- `anuncios/models.py` — `Anuncio` and `Preco`. UUID ids. No `conta` field. `anuncios/gravar.py` — the only upsert. `coleta` calls it.
- `anuncios/migrations/0001_initial.py` — tables, no RLS, DML grants to `rondimob_web` and `rondimob_worker`. Depend on `contas.0002_isolamento_da_conta`. Skip the SQL on SQLite.
- `coleta/tasks.py` — `coletar_zap` on queue `zap`. Load `coleta/fixtures/zap-exemplo.json` when the caller does not pass payloads. Print one stdout line. On failure, save `Falha` and do not raise into a half-written listing.
- `coleta/parser.py` — map the fixture fields and the three price strings. Do not fetch a URL.
- `config/settings.py` — `CELERY_TASK_ROUTES` for `coleta.tasks.coletar_zap`. Add both apps to `INSTALLED_APPS`.
- `config/celery.py` — autodiscover already imports installed apps. Do not collect inside a view.
- `config/urls.py` — do not add a collection route.
- `contas/cota.py` — do not call it from the task.
- `contas/tests/test_isolamento.py` — the RLS list is `contas_conta`, `contas_credito`, `radares_radar`. Keep it. The new tables stay off that list.
- `README.md` — the worker command already runs Celery. Say the ZAP task uses the queue `zap`, reads the fixture, and does not call the site. Live access waits until Rafael chooses how ZAP may be read.
- `sprint-status.yaml` — `2-2-editar-radar` `done`, `epic-2` `done`, `epic-3` `in-progress`, `3-1-coletar-o-zap-e-gravar-o-anúncio` `review`. Leave both retrospectives `optional` and `3-2` `backlog`.
- `deferred-work.md` — keep the signup race entry. Do not add a ZAP-credential entry.
- `MVP/`, `_bmad/`, `.agents/`, planning artifacts — do not change.

## Tasks & Acceptance

**Execution:**
- [x] `anuncios/models.py`, `anuncios/gravar.py`, `anuncios/migrations/0001_initial.py`, `coleta/parser.py`, `coleta/tasks.py`, `coleta/fixtures/zap-exemplo.json`, `config/settings.py` -- upsert a recorded ZAP payload on the `zap` queue -- the web request must not collect, and the corpus must not use RLS
- [x] `coleta/tests/test_zap.py`, `anuncios/tests/test_gravar.py` -- matrix on SQLite, worker grant on Postgres -- default `uv run pytest` still needs no Redis and no network
- [x] `README.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml` -- fixture note, 2.2 and epic 2 `done`, epic 3 `in-progress`, 3.1 `review`

**Acceptance Criteria:**
- Given the worker apart from the web, when ZAP collection runs, then it uses the ZAP queue, Celery 5.6.3 and the Redis broker, and it does not run inside the HTTP request. The migration is applied by `migrate`, the log line goes to stdout, and the worker process is the Celery command.
- Given a ZAP payload, when the worker stores it, then `anuncios` owns the listing and the price, `coleta` only delivers the payload, and the column types match the contract.
- Given "R$ 650.000", "650 mil" and "650000", when the worker stores the price, then all three are the same numeric.
- Given a stored listing with the same price, when collection repeats, then no second listing and no second price row are created, and the collection timestamp is updated. The key is fonte plus external id when present, otherwise the URL.
- Given the same listing with a different numeric price, when collection stores it, then a new price row is created.
- Given the ZAP collection, when it finishes or fails, then no account is debited and `RadarVisto` is not written, and the failure is stored.

## Implementation Notes

## Spec Change Log

## Review Triage Log

- BH1 — medium — `README.md` documents `celery -A config worker` with no `-Q`. Celery consumes only the `celery` queue by default, so `coletar_zap` routed to `zap` is never run. The "nothing publishes the task" clause is not a defect: this story reads the fixture when the task is called and does not add a scheduler.
- BH2 — low — two concurrent inserts of a new key can raise `IntegrityError`, which `coletar_zap` stores as `Falha`. Rejected: one worker and one recorded payload are the everyday path, and a lock plus retry adds branches the spec does not require.
- BH3 — false — a later payload that gains an external id is a different key under the frozen rule (fonte plus id when present, otherwise URL). A different URL string is a different key. `id` `0` and a blank `identificador_externo` next to `id` are unused by the fixture.
- BH4 — false — omitted listing fields become empty because the payload is the whole listing. A full payload on a price change writes those fields; it does not clear a previous full listing.
- BH5 — false — the contracted input is one object. A finished earlier row is not a half-written listing. Failure is a `Falha` row plus one stdout line, and the task does not have to raise.
- BH6 — low — `"+650.000"` skips the thousands-dot rule and `Decimal` stores `650.00`. Rejected: the three contracted strings (`R$ 650.000`, `650 mil`, `650000`) already parse to 650000, and sign, exponent, `NaN` area, and `"2.0"` room counts are not those inputs.
- BH7 — false — cidade is trimmed and casefolded because the frozen contract says so. Mapping to the radar's canonical ABCD name is a later story.
- BH8 — false — `WorkerGrantTests` inserts and selects as `rondimob_worker` and checks `relrowsecurity` is off. The socket patch did not fail the PostgreSQL suite, so the open test connection did not reconnect.
- EH1 — low — same signed-thousands parse as BH6. Rejected for the same reason.
- EH2 — low — `Decimal` accepts an exponent or underscore. Rejected: those tokens are not prices in the fixture or the three contracted strings.
- EH3 — low — `payload.get("identificador_externo", id)` keeps a blank explicit key and ignores `id`. Rejected: the fixture and tests use `id` alone or omit it.
- EH4 — false — same batch question as BH5. One recorded object does not leave a partial listing.
- EH5 — low — `list("")` is empty, so the task prints a zero count. Rejected: callers pass `None`, a dict, or a list, not a string.
- EH6 — low — same concurrent insert as BH2. Rejected for the same reason.
- EH7 — low — two workers can each insert a `Preco` row. Rejected: the story runs one task, and `select_for_update` is extra machinery.
- EH8 — medium — same unread `zap` queue as BH1.
- EH9 — false — the claim that a normal repeat with an external id inserts a second listing is disproved by `test_mesmo_preco_nao_duplica_e_move_o_instante`, which stores `650 mil` then `650000` for the same id and asserts one listing.
- VG1 — medium — `test_fixture_grava_um_anuncio_e_um_preco` never reads `endereco` or `descricao`, so dropping them from the parser stays green. Pre-verified. Patch: assert the fixture strings.
- VG2 — medium — no test stores two empty external ids with different URLs, so a key of fonte alone would still pass. Pre-verified. Patch: assert two rows.
- VG3 — medium — the failure test only raises on the first insert. Moving the price-change `save()` outside `atomic()` would leave the new price without a history row and still pass. Pre-verified. Patch: fail the second call and assert the original price remains.

Routed to patch: BH1+EH8 (README queue), VG1, VG2, VG3. No intent gap and no bad spec.

## Design Notes

The fixture is a small JSON file written for this story, not a copy of a ZAP page. The task accepts that payload in memory in tests. With no argument it reads the fixture file. It never opens a socket. Rafael later chooses whether ZAP is read from the public site or from an API, and supplies any key that choice needs. Until then the worker still runs the task on queue `zap`.

The first stored price creates the first `Preco` row. A repeat with the same numeric does not. `coletado_em` is `datetime.now(timezone.utc)`.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass on SQLite, without Redis and without the network
- `uv run pytest --ds config.postgres_settings` -- expected: pass, including the worker grant, against PostgreSQL
- `uv run python -c "import celery; print(celery.__version__)"` -- expected: `5.6.3`
