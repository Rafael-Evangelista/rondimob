---
title: 'Coletar a OLX sem parar o resto'
type: 'feature'
created: '2026-10-01'
status: 'in-progress'
route: 'dispatch'
baseline_commit: '8131938d688d01deeb664470cb960467d29f0684'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** ZAP and Viva Real are collected on their own queues. OLX still has nowhere to land, so one missing source is the whole market.

**Approach:** A third Celery task on its own queue reads a recorded OLX payload and calls the same upsert. Each task catches only its own error. Tests never call the site.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1, Celery 5.6.3, broker `redis://localhost:6379/0`. `coleta.tasks.coletar_olx` is routed to the queue `olx` and is not called from a view. It uses `anuncios.gravar.gravar` and `analisar(payload, fonte)` unchanged in signature. The OLX task passes `olx`. Price, area, rooms, baths, spaces, city, neighborhood, type, agency, and `coletado_em` stay on the 3.1 contract. "R$ 650.000", "650 mil" and "650000" are numeric 650000. The key stays fonte plus external id, or fonte plus URL. The same numeric price updates `coletado_em` only. A different numeric price adds one `Preco` row. An OLX failure writes one `Falha` with fonte `olx` and one stdout line, then returns without raising. A ZAP or Viva Real failure does not remove an OLX listing and does not stop `coletar_olx`. An OLX failure does not remove a ZAP or Viva Real listing and does not stop those tasks. After any of those failures, `GET /` still returns 200. A logged-in `GET /area/` and a radar POST do not create a listing. No account counter changes and `RadarVisto` is not written. The payload in tests is the fixture file, not a network response.

**Never:** Do not call OLX, ZAP, Viva Real, or any other site. Do not add credentials, tokens, or a live client. Do not add a parent task that runs the sources in one `try`. Do not implement stories 3.4 or 3.5. Do not spend quota or write `RadarVisto`. Do not put RLS on the corpus and do not add a migration. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts. Do not delete the existing `deferred-work.md` entry. Do not mark `epic-3-retrospective` done.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Recorded payload | Fixture `coleta/fixtures/olx-exemplo.json`, price "R$ 650.000", its own id and URL | One listing with fonte `olx` and one price row of 650000. Text is casefolded. `coletado_em` is UTC. A logged-in `GET /area/` and `POST /area/radares/novo/` before the task leave the listing count at 0. | A payload without URL writes `Falha` fonte `olx` and no listing. |
| Same upsert | Same external id, then "650 mil", then "700000" | The repeat keeps one price row and moves `coletado_em`. The new price leaves two price rows and listing price 700000. | N/A |
| Other queues fail | `coletar_zap` and `coletar_viva_real` each get a payload without URL, then `coletar_olx()` runs | The OLX fixture is stored. ZAP and Viva Real listings are absent. One `Falha` has fonte `zap` and one has fonte `viva-real`. | Those errors do not raise into the OLX call. |
| OLX fails | `coletar_olx` gets a payload without URL, then `coletar_zap()` and `coletar_viva_real()` run | The ZAP and Viva Real fixtures are stored. The OLX listing is absent. `GET /` is 200. A later OLX failure does not delete the other two listings. | The OLX error does not raise into the other calls. |
| Three fontes | Same external id and same URL, one payload per fonte | Three listings. The fonte is part of the key. | N/A |
| Quota | An account exists. The OLX task runs | Free, month, and credit counters stay unchanged. No `RadarVisto` model is written. | N/A |
| SQLite | `uv run pytest` | These tests pass without Redis and without the network. | N/A |

</frozen-after-approval>

## Code Map

- `anuncios/gravar.py` — `gravar` already keys on `dados["fonte"]`. Do not change it.
- `coleta/parser.py` — `analisar(payload, fonte)` already writes that fonte. Do not change the signature. Do not fetch a URL.
- `coleta/tasks.py` — `coletar_zap` and `coletar_viva_real` already pass their own fonte and catch only their own error. Add `coletar_olx` on queue `olx`. With no argument it reads `coleta/fixtures/olx-exemplo.json`. Its `except` saves `Falha` and does not raise. Do not wrap the three tasks in one function. Reuse `_carregar`.
- `coleta/fixtures/olx-exemplo.json` — synthetic JSON for this story, not a copy of an OLX page. Different id and URL from the ZAP and Viva Real fixtures.
- `coleta/models.py` — `Falha.fonte` already holds the source name. No new model and no migration.
- `config/settings.py` — add `CELERY_TASK_ROUTES["coleta.tasks.coletar_olx"]` to queue `olx`. Leave the ZAP and Viva Real routes.
- `config/celery.py` — autodiscover already imports the app. Do not collect inside a view.
- `config/urls.py`, `contas/views.py`, `radares/views.py`, `contas/cota.py` — do not call the new task and do not add a route.
- `contas/tests/test_isolamento.py` — the RLS list stays `contas_conta`, `contas_credito`, `radares_radar`.
- `README.md` — worker command `-Q celery,zap,viva-real,olx`. Say the OLX task reads its fixture, does not call the site, and a failure on one queue does not cancel the others. Live access waits until Rafael chooses how OLX may be read.
- `sprint-status.yaml` — `3-2-coletar-a-viva-real-sem-parar-o-resto` `done`, `epic-3` `in-progress`, `3-3-coletar-a-olx-sem-parar-o-resto` `review`. Leave `3-4` `backlog` and `epic-3-retrospective` `optional`.
- `deferred-work.md` — keep the signup race entry. Do not add a credential entry.
- `MVP/`, `_bmad/`, `.agents/`, planning artifacts — do not change.

## Tasks & Acceptance

**Execution:**
- [x] `coleta/tasks.py`, `coleta/fixtures/olx-exemplo.json`, `config/settings.py` -- record an OLX payload on queue `olx` through the existing upsert -- the web request must not collect, and one task must not catch the others
- [x] `coleta/tests/test_olx.py` -- matrix on SQLite, including both failure orders, the logged-in area, and `GET /` -- default `uv run pytest` still needs no Redis and no network
- [x] `README.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml` -- fixture note and queue flag, 3.2 `done`, epic 3 `in-progress`, 3.3 `review`

**Acceptance Criteria:**
- Given the OLX queue, when collection runs, then the payload uses the same contract and the same `anuncios` upsert, and it does not run inside the HTTP request.
- Given a failure on the Viva Real queue or the ZAP queue, when the OLX queue runs, then OLX finishes or records its own error, and the other queues and the site still respond.
- Given a failure on the OLX queue, when the ZAP and Viva Real queues run, then those sources still store their fixtures, and the site still responds.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

The fixture is synthetic JSON, not an OLX page. With no argument the task reads that file and never opens a socket. Rafael later chooses whether OLX is read from the public site or from an API, and supplies any key that choice needs. Until then the worker still runs the task on queue `olx`.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass on SQLite, without Redis and without the network
- `uv run pytest --ds config.postgres_settings` -- expected: pass against PostgreSQL
- `uv run python -c "import celery; print(celery.__version__)"` -- expected: `5.6.3`
