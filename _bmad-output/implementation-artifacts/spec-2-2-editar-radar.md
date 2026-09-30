---
title: 'Editar radar'
type: 'feature'
created: '2026-09-30'
status: 'in-review'
route: 'dispatch'
baseline_commit: '124a8177bdd0e76f24343d3a384f571185acf35a'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A saved radar cannot be corrected. Changing a filter would require another radar, and nothing stops one account from opening another's radar.

**Approach:** Reuse the create form on the same radar row. An invalid city saves nothing. The edit is limited to the account that owns the row and does not spend a search.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1. `GET` and `POST /area/radares/<uuid>/` edit that radar. The form is `RadarForm` with the existing instance, so city, text, range, and negative-bound rules stay the ones from creation. A valid save updates bairro, tipo, preço, área, quartos, vagas, imobiliária, and a cidade inside the ABCD. The primary key and the row count stay the same. A cidade outside the ABCD, or any other invalid form, writes nothing: the previous cidade and the other stored filters remain. Account A posting account B's id gets 404 and B's row is unchanged. The lookup filters by `request.user`, so the owner database connection cannot bypass that. Anonymous POST redirects to `/entrar/`. `GET` does not write. Editing does not change the free counter, the month counter, or the credit balance, including when the free trial is closed. Each radar label on `/area/` links to its edit page. Postgres still proves the web role cannot update another account's radar.

**Never:** Do not add a migration, a column, or a second RLS policy. Do not implement Epic 3, and do not run a search or spend quota. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts. Do not delete the existing `deferred-work.md` entry. Do not mark `epic-2-retrospective` done. Do not set `epic-2` to `done` while 2.2 is `review`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Edit filters | One radar. POST new bairro, tipo, both prices, both areas, quartos, vagas, and imobiliária | Same id. One row. Stored filters and the area label change. Counters stay unchanged. | Anonymous POST redirects to `/entrar/`. |
| City inside ABCD | Same radar. POST cidade Diadema | Same id. `cidade` becomes Diadema. | N/A |
| City outside | Same radar. POST cidade São Paulo, plus other new filters | No column changes. The form is shown again. | N/A |
| Other account | Two accounts. A posts B's radar id | 404. B's filters stay as they were. | N/A |
| Closed trial | Free account, 10 searches used | POST still updates the radar. The free counter stays 10. Search, favorite, and alert stay closed. | N/A |
| SQLite | `uv run pytest` | Edit tests pass. The existing web-role isolation test skips. | N/A |

</frozen-after-approval>

## Code Map

- `radares/forms.py` — reuse `RadarForm`. Do not copy the city or range checks. `save(conta)` already updates an instance that has a primary key.
- `radares/views.py` — add `editar`. Load `Radar` with `pk` and `conta=request.user`, or 404. GET binds the instance. Valid POST saves and redirects to `/area/`. Invalid POST re-renders and does not write.
- `radares/templates/radares/novo.html` — the create page hardcodes the action and the title. Pass the title and the action from the view so create stays `Novo radar` at `/area/radares/novo/` and edit says `Editar radar`.
- `config/urls.py` — add `area/radares/<uuid:radar_id>/` beside `area/radares/novo/`. The uuid converter does not match `novo`.
- `contas/templates/contas/area.html` — each label links to that radar's edit URL. Keep `Novo radar`.
- `contas/views.py` — the list currently comes from `nomes_de_radar`, which returns strings. Give the template the id as well as the label. `contas/tests/test_cota.py` patches `contas.views.nomes_de_radar` with `["Radar Centro"]`. Update that test so a real radar still shows its label on the closed trial and the free counter stays 0.
- `contas/cota.py` — keep `nomes_de_radar` ordered by `criado_em`, then `id`, if anything still calls it.
- `radares/tests/test_radar.py` — creation tests must keep passing, including the create form action.
- `contas/tests/test_isolamento.py` — leave the web-role radar test and the `contas_conta` policy as they are.
- `README.md` — say an edit updates the same radar, does not spend a search, and a city outside the ABCD leaves the stored city.
- `sprint-status.yaml` — `2-1-criar-radares-no-abcd` `done`, `2-2-editar-radar` `review`. Leave `epic-2` `in-progress` and `epic-2-retrospective` `optional`.
- `deferred-work.md` — keep the signup race entry.
- `MVP/`, `_bmad/`, `.agents/`, planning artifacts — do not change.

## Tasks & Acceptance

**Execution:**
- [x] `radares/views.py`, `radares/templates/radares/novo.html`, `config/urls.py`, `contas/templates/contas/area.html`, `contas/views.py` -- edit the same radar from the area list -- reuse `RadarForm` and do not spend a search
- [x] `radares/tests/test_editar.py`, `contas/tests/test_cota.py` -- matrix on SQLite, including another account's id -- default `uv run pytest` still needs no Postgres
- [x] `README.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml` -- edit note, 2.1 `done`, 2.2 `review`, retrospective left `optional`

**Acceptance Criteria:**
- Given a radar of the account, when it changes bairro, tipo, price range, area range, quartos, vagas, or the announcing agency and saves, then the same radar has the new filters, no second radar is created, and no search is spent.
- Given a city outside the ABCD, when the account saves the edit, then the radar keeps its previous city.
- Given account B's radar, when account A tries to edit it, then B's radar does not change.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

An invalid city rejects the whole POST. A partial write would keep the new bairro beside the old city. The edit page reuses the create fields and the same error text. Story 2.1's web-role test remains the RLS proof; this story adds the account filter on the HTTP lookup because the test database owner bypasses `FORCE ROW LEVEL SECURITY`.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass on SQLite, web-role isolation skipped
- `uv run pytest --ds config.postgres_settings` -- expected: pass, including the existing radar isolation test, against PostgreSQL
- `uv run python -c "import django; print(django.get_version())"` -- expected: `6.1.1`
