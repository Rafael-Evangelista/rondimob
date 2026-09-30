---
title: 'Usar o grátis e ver o bloqueio'
type: 'feature'
created: '2026-09-30'
status: 'done'
route: 'dispatch'
baseline_commit: '0f7603ece3be85925979a37c426a04582a178ed7'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A new account has no free-trial counter and no block. The area does not say how many searches remain, and nothing refuses a search after 10 uses or on the 15th calendar day.

**Approach:** Keep the counter on `contas_conta`, under the existing `conta_isola` policy. A gate in `contas` accepts or refuses a search and is what later stories call before search, favorite, and alert. The area shows the remaining free searches, and when the trial is over it shows the plans and any radar names that already exist.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1. Free trial is 10 searches and 14 calendar days from the account's creation date in `America/Sao_Paulo`. The creation local date is day 1. The last open day is that date plus 13 days. The next date is the 15th day and is blocked. `contas.cota.aceitar_pesquisa` is the only writer of the counter. It uses `select_for_update` inside `transaction.atomic` and sets `app.conta_id` before the read. Signup, login, logout, `GET /`, and `GET /area/` do not consume a search. While the trial is open, `/area/` shows remaining searches and the last open date. When blocked, `/area/` shows the four portal plans and the radar names from `nomes_de_radar` (empty until epic 2). The gate functions `pode_pesquisar`, `pode_favoritar`, and `pode_configurar_alerta` are false in the blocked state and true while the trial is open. New columns have database defaults so the existing raw inserts in the isolation tests still succeed. Postgres tests prove account A cannot read B's counter.

**Never:** Do not activate Padrão, Plus, or Personalizado, and do not store a paid plan or a monthly quota (story 1.6). Do not add credit balance, a credit table, or a reload (story 1.7). Do not create radar, favorito, alerta, visto, or envio tables, and do not execute a real search. Do not add a second RLS policy; the new columns stay on `contas_conta`. Do not change signup field rules or the recovery boundary. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts. Do not delete the existing `deferred-work.md` entry.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| New account | Created without a paid plan. `GET /area/` | Page shows 10 searches remaining and the last open date (creation local date + 13 days). Counter stays 0. | Anonymous `GET /area/` still redirects to `/entrar/`. |
| Accepted search | Trial open, 3 already used. `aceitar_pesquisa` | Counter becomes 4. A second call in the same state is the only other decrement. | N/A |
| No spend | Signup, login, `GET /`, `GET /area/` | Counter stays 0. | N/A |
| Tenth and eleventh | 9 used, trial open | The 10th call returns true and the counter is 10. The 11th returns false and the counter stays 10. `pode_pesquisar`, `pode_favoritar`, and `pode_configurar_alerta` are false. | N/A |
| Day 14 and day 15 | Creation local date D. Today is D+13, then D+14. Zero uses. | D+13 accepts a search. D+14 refuses, counter stays 0, and `/area/` shows the plans (Grátis, Padrão, Plus, Personalizado with the portal prices) plus the radar section. | N/A |
| Zone edge | `criada_em` is 2026-09-01 02:30 UTC | Creation local date is 2026-08-31. Last open day is 2026-09-13. | N/A |
| Other account | Two accounts on PostgreSQL. Web role, `app.conta_id` is A. | Select returns A's counter only. Updating B's counter changes no row. | N/A |
| SQLite | `uv run pytest` | Page and gate tests pass. The Postgres isolation test skips. | N/A |

</frozen-after-approval>

## Code Map

- `contas/models.py` — `Conta` and `Conta.save`, which already calls `definir_conta` before write. Add `criada_em` and `pesquisas_gratis_usadas`. Do not add a plan or credit field.
- `contas/cota.py` — new gate. `aceitar_pesquisa` is the only counter writer. `nomes_de_radar` returns an empty list.
- `contas/views.py` — `area` renders the trial state. Do not decrement there. Leave signup, login, and recovery as they are.
- `contas/templates/contas/area.html` — name, logout, remaining searches or the block with plans. Reuse the portal price strings.
- `contas/migrations/0002_isolamento_da_conta.py` — policy `conta_isola` already covers every column of `contas_conta`. Add `0003` for the two columns only. No new `ENABLE`/`FORCE`.
- `contas/tests/test_isolamento.py` — raw `INSERT` lists columns and relies on database defaults for the rest. Keep that insert working.
- `contas/tests/test_sessao.py` — login and area assertions must keep passing. Area will gain trial copy.
- `config/settings.py` — `TIME_ZONE` is `America/Sao_Paulo`. The gate still names that zone itself.
- `config/test_settings.py` — SQLite overlay. Keep the default pytest run here.
- `README.md` — say what the free trial shows and that the counter isolation runs with the Postgres suite.
- `sprint-status.yaml` — set `1-4-uma-conta-não-lê-a-outra` to `done` and `1-5-usar-o-grátis-e-ver-o-bloqueio` to `review` when the code is finished.
- `deferred-work.md` — keep the signup race entry.
- `MVP/`, `_bmad/`, `.agents/`, planning artifacts — do not change.

## Tasks & Acceptance

**Execution:**
- [x] `contas/models.py`, `contas/migrations/0003_cota_gratis.py` -- add the creation timestamp and the free counter with database defaults -- the existing policy has to cover them and old inserts have to keep working
- [x] `contas/cota.py`, `contas/views.py`, `contas/templates/contas/area.html` -- gate plus the area copy -- future stories call the gate, and opening the area must not spend a search
- [x] `contas/tests/test_cota.py`, `contas/tests/test_isolamento.py` -- matrix on SQLite, counter isolation on Postgres -- default `uv run pytest` still needs no Postgres
- [x] `README.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml` -- trial note, 1.4 `done`, 1.5 `review` -- 1.4 is already merged

**Acceptance Criteria:**
- Given a new account without a paid plan, when it opens the area, then the free trial is 14 calendar days from the creation date in America/Sao_Paulo, with at most 10 searches, and only `contas` changes that counter.
- Given the account is still in the window with searches left, when a search is accepted, then the counter decreases by one, and creating an account, entering the area, and opening the plans page do not spend a search.
- Given the 15th day without a paid plan, or 10 searches already used, when the account enters, then it sees radar names that already exist and the plans, and it does not execute a search, favorite, or configure an alert.
- Given search, favorite, and alert have no screen yet, when this story ends, then `contas` exposes the gate those stories will call, and the paid-plan quota is not implemented.

## Implementation Notes

## Spec Change Log

## Review Triage Log

- `low` — README “14th calendar day from the creation date” can be read as creation plus 14, and the counter sentence reads as if both roles run that check. The gate uses creation as day 1 and the counter test uses `rondimob_web`. Route: patch.
- `false` — the spec says the counter decreases while the column increases — the column counts uses; the area remainder goes from 10 toward 0. Three used becoming 4 is the column. Not a code defect.
- `medium` — `pesquisas_restantes` ignores the calendar window and still returns a positive count on the 15th day. `/area/` hides it by branching on `pode_pesquisar`. A later caller can show searches left after the trial date. Route: patch.
- `low` — the blocked area has no “trial over” sentence and an empty radar list — the plans are the ask, and no radar names exist yet. Rejected.
- `low` — `Conta.save()` can persist a stale counter — current writes use `update_fields` or `aceitar_pesquisa`. Rejected: guarding every save adds a branch no current caller hits.
- `low` — `Now()` at migrate time starts the window for rows that predate the column — this app has no production accounts yet, and new signups stamp `criada_em` at creation. Rejected.
- `medium` — tests never desync the in-memory account from the locked row, so `aceitar_pesquisa` could trust the caller and still pass. The current function uses the locked row. Route: patch.
- edge-case layer returned no findings.

## Design Notes

Day 1 is the creation date in `America/Sao_Paulo`, not a 336-hour window. An account created at 2026-09-01 02:30 UTC belongs to 2026-08-31 locally and is blocked starting 2026-09-14.

`aceitar_pesquisa` returns false without writing when the trial is blocked. There is no search button. `nomes_de_radar` stays empty until a later epic adds radars.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass on SQLite, Postgres counter isolation skipped
- `uv run pytest --ds config.postgres_settings` -- expected: pass, including the counter isolation, against PostgreSQL
- `uv run python -c "import django; print(django.get_version())"` -- expected: `6.1.1`
