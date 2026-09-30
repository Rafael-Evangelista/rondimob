---
title: 'Criar radares no ABCD'
type: 'feature'
created: '2026-09-30'
status: 'done'
route: 'dispatch'
baseline_commit: '1e543aa7f6d4992032d252043c6edf4f42e2db18'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** An authenticated account cannot save what it wants to monitor. The area list of radar names is empty, including after the free trial closes.

**Approach:** Add a `radares` app and one form. Saving stores the filters on that account. A second save keeps both. Creation does not spend a search. The radar table is isolated by RLS.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1. One form, no wizard, at `POST /area/radares/novo/`. Fields: imobiliária anunciante, cidade, bairro, tipo, preço mínimo, preço máximo, área mínima, área máxima, quartos mínimos, vagas mínimas. Only cidade is required. Cidade accepts Santo André, São Bernardo do Campo, São Caetano do Sul, or Diadema, including case and missing accents, and stores the canonical name. Any other city creates nothing. Bairro and área máxima may be blank; the Santo André example omits them. Other text is stored casefolded and trimmed. Preço and área are `numeric`; quartos and vagas are integers. The example stores imobiliária, Santo André, apartamento, 300000 to 800000, 60 m², 2 quartos, and 1 vaga. The area lists each radar as cidade, tipo, and imobiliária, skipping blanks. A second radar stays in the list. Creating does not change the free counter, the month counter, or the credit balance, including when the free trial is closed. The table uses `ENABLE` and `FORCE ROW LEVEL SECURITY`, a UUID id, and a policy that reads only `app.conta_id`. Postgres proves account A cannot read account B's radar.

**Never:** Do not implement story 2.2 or an edit route. Do not run a search, spend quota, or create anúncio, favorito, alerta, visto, or envio tables. Do not add a column on `contas_conta` or a second policy there. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts. Do not delete the existing `deferred-work.md` entry. Do not mark either retrospective done.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Example | Authenticated. One POST with Alfa, Santo André, blank bairro, apartamento, 300000, 800000, 60, blank área máxima, 2, 1 | One radar stores those filters. `/area/` lists `Santo André · apartamento · alfa`. Counters stay unchanged. | Anonymous POST redirects to `/entrar/`. |
| Outside ABCD | Cidade São Paulo, or blank | No radar row. The form is shown again. | N/A |
| Second radar | Account already has one radar | Both labels stay on `/area/`. Counters stay unchanged. | N/A |
| Closed trial | Free account, 10 searches used | POST still creates the radar. `pesquisas_gratis_usadas` stays 10. Search, favorite, and alert stay closed. The blocked area lists the radar. | N/A |
| Other account | PostgreSQL, web role, `app.conta_id` is A | Select returns A's radar only. Updating B's radar changes no row. | N/A |
| SQLite | `uv run pytest` | Create and quota tests pass. Radar isolation skips. | N/A |

</frozen-after-approval>

## Code Map

- `radares/` — new app. `Radar` has a UUID pk, FK to `Conta`, the filter columns, and `criado_em`. `save` calls `definir_conta` before the write, as `Credito.save` does. `rotulo` joins cidade, tipo, and imobiliária.
- `radares/forms.py` — one form. Map the four cities to canonical names. Reject anything else. Casefold the other text. Reject a max below its min. Do not call `aceitar_pesquisa`.
- `radares/views.py`, `radares/templates/radares/novo.html` — GET shows the form. Valid POST saves and redirects to `/area/`. Invalid POST re-renders the same form.
- `config/settings.py` — add `radares` to `INSTALLED_APPS`.
- `config/urls.py` — add `area/radares/novo/` next to the area routes.
- `contas/cota.py` — `nomes_de_radar` returns the account's labels ordered by `criado_em`. Keep the function name; `contas/views.py` already imports it.
- `contas/templates/contas/area.html` — every authenticated state lists `radares` and links to the form with `Novo radar`. The blocked state already has the Radares section; fill it from `nomes_de_radar` and keep the plan cards.
- `contas/tests/test_cota.py` — `test_new_account_shows_ten_searches_and_the_last_open_day` forbids the heading `Radares` on an open trial. Change that assertion so an empty list may show, and still forbid `R$ 97 por mês`. Do not weaken the closed-trial assertions that an empty list has no `<li>`.
- `radares/migrations/0001_initial.py` — create the table, grant DML to `rondimob_web` and `rondimob_worker`, and `ENABLE`/`FORCE` plus policy `conta_isola` on `radares_radar` only. Skip that SQL on SQLite. The migrate role owns the table.
- `contas/tests/test_isolamento.py` — the RLS table list must also include `radares_radar`. Extend `_apagar` so a radar row cannot block deleting the account. Leave the `contas_conta` policy unchanged.
- `README.md` — one form creates a radar in the ABCD, a second one stays, and creation does not spend a search.
- `sprint-status.yaml` — `1-7-recarregar-créditos` `done`, `epic-1` `done`, `epic-2` `in-progress`, `2-1-criar-radares-no-abcd` `review`. Leave both retrospectives `optional` and `2-2-editar-radar` `backlog`.
- `deferred-work.md` — keep the signup race entry.
- `MVP/`, `_bmad/`, `.agents/`, planning artifacts — do not change.

## Tasks & Acceptance

**Execution:**
- [x] `radares/models.py`, `radares/migrations/0001_initial.py`, `config/settings.py` -- radar table with UUID filters and its own RLS -- another account's radar stays hidden
- [x] `radares/forms.py`, `radares/views.py`, `radares/templates/radares/novo.html`, `config/urls.py`, `contas/cota.py`, `contas/templates/contas/area.html` -- one ABCD form and the account's list -- creation must not spend a search, and a closed trial can still create
- [x] `radares/tests/test_radar.py`, `contas/tests/test_isolamento.py`, `contas/tests/test_cota.py` -- matrix on SQLite, radar isolation on Postgres -- default `uv run pytest` still needs no Postgres
- [x] `README.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml` -- ABCD note, 1.7 and epic 1 `done`, epic 2 `in-progress`, 2.1 `review`

**Acceptance Criteria:**
- Given an authenticated account, when it submits the single form, then the radar is stored on that account and appears in its list, with no step beyond the form.
- Given Santo André, apartamento, R$ 300.000 to R$ 800.000, 2 quartos, 60 m², 1 vaga, and an announcing agency, when the account saves, then the radar stores those filters, and a city outside the four ABCD names is not stored.
- Given an account that already has one radar, when it creates another, then both remain in the list, and creating a radar does not spend a search.
- Given the radar table, when account A lists radars, then it does not see account B's radar, and the table uses `ENABLE` and `FORCE ROW LEVEL SECURITY` with a UUID id.

## Implementation Notes

## Spec Change Log

## Review Triage Log

- `medium` — `radares.0001` depends only on `contas.0001`. `migrate radares` grants to `rondimob_web` before `contas.0002` creates those roles. Route: patch, depend on `contas.0002_isolamento_da_conta`.
- `low` — a negative price or area is stored. Route: patch, reject a bound below zero in `RadarForm` and cover it with a test. Quartos and vagas already use `PositiveIntegerField`.
- `false` — an inverted range is not stored through the form. `_rejeitar_faixa` adds the error and the template renders that field's errors. The test already expects no row. A raw insert in the isolation helper is not a product writer.
- `false` — the example is the decimal values 300000, 800000, and 60, which the form accepts. The prose "R$ 300.000" is not the posted string. The labels match the form fields.
- `false` — an anonymous browser POST without a CSRF token is rejected by `CsrfViewMiddleware` before the view, the same way as the other area posts. The view redirects to `/entrar/` when the request reaches it, and it does not save.
- `low` — the radar suite does not also assert DELETE, a foreign insert, or the worker role. The policy `WITH CHECK` is `conta_id` equals `app.conta_id`, and the web-role test already shows A cannot read or update B. Rejected: more DML cases are extra tests.
- `false` — `nomes_de_radar` during `GET /area/` runs inside `IsolamentoDaContaMiddleware`, which sets `app.conta_id` before the view. `Radar.save` also sets it before the insert.
- `false` — a blank city creates no row and shows the form again. Cidade is required, so the empty value fails before the ABCD check. The control is text because the spec accepts case and missing accents, not a fixed dropdown.
- `false` — creation does not call `aceitar_pesquisa`, so the calendar day cannot spend a search or block the save. The closed-trial test already keeps the free counter at 10 and the search, favorite, and alert gates shut.
- `low` — two radars with the same `criado_em` are ordered only by that timestamp. Route: patch, order by `criado_em`, then `id`.
- `low` — the form page has no link back to the area. Rejected: the browser returns to the area, and adding a link is extra navigation the form does not need.
- edge-case layer returned the negative bound and the same-timestamp order. verification-gap layer returned no findings.

## Design Notes

The list label is derived because the form has no name field. `Santo André · apartamento · alfa` is the example. A closed free account can create; the gates that stay closed are search, favorite, and alert. Story 2.2 owns editing.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass on SQLite, radar isolation skipped
- `uv run pytest --ds config.postgres_settings` -- expected: pass, including radar isolation, against PostgreSQL
- `uv run python -c "import django; print(django.get_version())"` -- expected: `6.1.1`
