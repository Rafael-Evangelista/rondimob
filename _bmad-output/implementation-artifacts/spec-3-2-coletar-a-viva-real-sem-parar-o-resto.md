---
title: 'Coletar a Viva Real sem parar o resto'
type: 'feature'
created: '2026-10-01'
status: 'in-review'
route: 'dispatch'
baseline_commit: '70cd62971993db2f76ee01c561439f960a1968f7'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Only ZAP is collected. A failure on that queue would be the whole corpus, and Viva Real has nowhere to land.

**Approach:** A second Celery task on its own queue reads a recorded Viva Real payload and calls the same upsert. Each task catches only its own error. Tests never call the site.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1, Celery 5.6.3, broker `redis://localhost:6379/0`. `coleta.tasks.coletar_viva_real` is routed to the queue `viva-real` and is not called from a view. It uses `anuncios.gravar.gravar` unchanged. `analisar(payload, fonte)` sets `fonte` to the argument; the Viva Real task passes `viva-real` and the ZAP task passes `zap`. Price, area, rooms, baths, spaces, city, neighborhood, type, agency, and `coletado_em` stay on the 3.1 contract. "R$ 650.000", "650 mil" and "650000" are numeric 650000. The key stays fonte plus external id, or fonte plus URL. The same numeric price updates `coletado_em` only. A different numeric price adds one `Preco` row. A Viva Real failure writes one `Falha` with fonte `viva-real` and one stdout line, then returns without raising. A ZAP failure does not remove a Viva Real listing, and a Viva Real failure does not remove a ZAP listing. After either failure, `GET /` still returns 200. No account counter changes and `RadarVisto` is not written. The payload in tests is the fixture file, not a network response.

**Never:** Do not call Viva Real, ZAP, OLX, or any other site. Do not add credentials, tokens, or a live client. Do not add a parent task that runs both sources in one `try`. Do not implement stories 3.3 through 3.5. Do not spend quota or write `RadarVisto`. Do not put RLS on the corpus and do not add a migration. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts. Do not delete the existing `deferred-work.md` entry. Do not mark `epic-3-retrospective` done.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Recorded payload | Fixture `coleta/fixtures/viva-real-exemplo.json`, price "650 mil", its own id and URL | One listing with fonte `viva-real` and one price row of 650000. Text is casefolded. `coletado_em` is UTC. No HTTP view created it. | A payload without URL writes `Falha` fonte `viva-real` and no listing. |
| Same upsert | Same external id, then "R$ 650.000", then "700000" | The repeat keeps one price row and moves `coletado_em`. The new price leaves two price rows and listing price 700000. | N/A |
| ZAP fails first | `coletar_zap` gets a payload without URL, then `coletar_viva_real()` runs | The Viva Real fixture is stored. The ZAP listing is absent. One `Falha` has fonte `zap`. | The ZAP error does not raise into the Viva Real call. |
| Viva Real fails first | `coletar_viva_real` gets a payload without URL, then `coletar_zap()` runs | The ZAP fixture is stored. The Viva Real listing is absent. One `Falha` has fonte `viva-real`. `GET /` is 200. | The Viva Real error does not raise into the ZAP call. |
| Two fontes | Same external id and same URL, one payload per fonte | Two listings. The fonte is part of the key. | N/A |
| Quota | An account exists. The Viva Real task runs | Free, month, and credit counters stay unchanged. No `RadarVisto` model is written. | N/A |
| SQLite | `uv run pytest` | These tests pass without Redis and without the network. | N/A |

</frozen-after-approval>

## Code Map

- `anuncios/gravar.py` — `gravar` already keys on `dados["fonte"]`. Do not change it.
- `coleta/parser.py` — `analisar(payload, fonte)` writes that fonte. Keep the price and text rules. Do not fetch a URL.
- `coleta/tasks.py` — `coletar_zap` passes `zap`. Add `coletar_viva_real` on queue `viva-real`. With no argument it reads `coleta/fixtures/viva-real-exemplo.json`. Its `except` saves `Falha` and does not raise. Do not wrap both tasks in one function.
- `coleta/fixtures/viva-real-exemplo.json` — synthetic JSON for this story, not a copy of a Viva Real page. Different id and URL from the ZAP fixture.
- `coleta/models.py` — `Falha.fonte` already holds the source name. No new model and no migration.
- `config/settings.py` — add `CELERY_TASK_ROUTES["coleta.tasks.coletar_viva_real"]` to queue `viva-real`.
- `config/celery.py` — autodiscover already imports the app. Do not collect inside a view.
- `config/urls.py`, `contas/views.py`, `radares/views.py`, `contas/cota.py` — do not call the new task and do not add a route.
- `contas/tests/test_isolamento.py` — the RLS list stays `contas_conta`, `contas_credito`, `radares_radar`.
- `README.md` — worker command `-Q celery,zap,viva-real`. Say the Viva Real task reads its fixture, does not call the site, and a failure on one queue does not cancel the other. Live access waits until Rafael chooses how Viva Real may be read.
- `sprint-status.yaml` — `3-1-coletar-o-zap-e-gravar-o-anúncio` `done`, `epic-3` `in-progress`, `3-2-coletar-a-viva-real-sem-parar-o-resto` `review`. Leave `3-3` `backlog` and `epic-3-retrospective` `optional`.
- `deferred-work.md` — keep the signup race entry. Do not add a credential entry.
- `MVP/`, `_bmad/`, `.agents/`, planning artifacts — do not change.

## Tasks & Acceptance

**Execution:**
- [x] `coleta/parser.py`, `coleta/tasks.py`, `coleta/fixtures/viva-real-exemplo.json`, `config/settings.py` -- record a Viva Real payload on queue `viva-real` through the existing upsert -- the web request must not collect, and one task must not catch the other
- [x] `coleta/tests/test_viva_real.py` -- matrix on SQLite, including both failure orders and `GET /` -- default `uv run pytest` still needs no Redis and no network
- [x] `README.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml` -- fixture note and queue flag, 3.1 `done`, epic 3 `in-progress`, 3.2 `review`

**Acceptance Criteria:**
- Given the Viva Real queue, when collection runs, then the payload uses the 3.1 contract and the same `anuncios` upsert, and it does not run inside the HTTP request.
- Given a failure on the ZAP queue, when the Viva Real queue runs, then Viva Real finishes or records its own error, and the site still responds.
- Given a failure on the Viva Real queue, when the ZAP queue runs, then ZAP still stores its fixture, and the site still responds.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

The fixture is a small JSON file written for this story. The task accepts that payload in memory in tests. With no argument it reads the fixture file. It never opens a socket. Rafael later chooses whether Viva Real is read from the public site or from an API, and supplies any key that choice needs. Until then the worker still runs the task on queue `viva-real`.

Isolation is two tasks and two queues. There is no parent task. Each `except` belongs to one function, so a recorded failure cannot cancel the other source or the Django site.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass on SQLite, without Redis and without the network
- `uv run pytest --ds config.postgres_settings` -- expected: pass against PostgreSQL
- `uv run python -c "import celery; print(celery.__version__)"` -- expected: `5.6.3`
