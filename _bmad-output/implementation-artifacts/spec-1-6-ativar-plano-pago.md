---
title: 'Ativar plano pago'
type: 'feature'
created: '2026-09-30'
status: 'in-progress'
route: 'dispatch'
baseline_commit: 'cbf372e58a27d20f3a9805ede52196632e89e623'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A blocked free account cannot start a paid quota. Nothing records Padrão or Plus, and the month does not reset the search count.

**Approach:** Store the plan and the monthly counter on `contas_conta`, under the existing `conta_isola` policy. Activation is a state change in the web request. No payment gateway is called. The free-trial gate stays for accounts with no paid plan.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1. Padrão is 30 searches in the America/Sao_Paulo calendar month at R$ 97. Plus is 100 searches in that month at R$ 197. The same monitoring gate applies to both. Personalizado shows a contact line and does not save a plan or a quota. `plano` is `padrao` or `plus`; empty means the free trial. `mes_da_cota` is the first day of the current local month. Leftover searches do not carry into the next month: a different month ignores `pesquisas_mes_usadas` and the next accepted search starts again at 1 of 30 or 100. First activation of a plan sets that month's used count to 0. Switching plans in the same month keeps the used count and changes only the cap. At 0 remaining and no credit balance, `aceitar_pesquisa` returns false and `/area/` shows the saved-results section (`resultados_gravados` is empty). `pode_favoritar` and `pode_configurar_alerta` are true while Padrão or Plus is active, including at 0 searches. New columns have database defaults or are nullable so existing raw inserts still succeed. Postgres tests prove account A cannot read B's plan or monthly counter. Authenticated `POST /area/plano/` with `plano=padrao` or `plano=plus` activates. `GET /area/` does not spend a search.

**Never:** Do not call Mercado Pago, Stripe, or any other gateway, and do not add credentials or a fake charge. Do not add a credit table, a reload, or a R$ 47 balance (story 1.7). Do not create radar, favorito, alerta, visto, or envio tables, and do not execute a real search. Do not store Personalizado as an active plan. Do not add a second RLS policy. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts. Do not delete the existing `deferred-work.md` entry.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Activate Padrão | Authenticated. `POST /area/plano/` `plano=padrao` | `plano` is `padrao`, used this month is 0, remaining is 30. No gateway module is imported. | Anonymous POST redirects to `/entrar/`. |
| Activate Plus | Authenticated, possibly already on Padrão with 5 used | `plano` is `plus`, used stays 5, remaining is 95. | N/A |
| Personalizado | Authenticated opens the area and posts `plano=personalizado` | Page says the plan is by contact. `plano` and the counters stay unchanged. | N/A |
| Month turn | Plus, January used 10. Clock moves to 1 February | Remaining is 100. The next accepted search leaves used at 1 for February. January's leftover is not added. | N/A |
| Quota empty | Padrão, 30 used, same month, no credit | `aceitar_pesquisa` returns false. `/area/` shows Resultados and does not spend. Favorite and alert gates stay true. | N/A |
| Free trial kept | No plan, day 1, 0 used | Area still shows 10 free searches. Accepting one search increments only `pesquisas_gratis_usadas`. | N/A |
| Other account | Two accounts on PostgreSQL. Web role, `app.conta_id` is A | Select returns A's `plano` only. Updating B's plan changes no row. | N/A |
| SQLite | `uv run pytest` | Activation and month tests pass. The plan isolation test skips. | N/A |

</frozen-after-approval>

## Code Map

- `contas/cota.py` — free-trial gate and `aceitar_pesquisa`, the only search-counter writer. Extend it so a paid plan spends `pesquisas_mes_usadas` and a closed trial still spends `pesquisas_gratis_usadas`. Add `ativar_plano`.
- `contas/models.py` — `Conta`. Add `plano`, `pesquisas_mes_usadas`, and `mes_da_cota`. Do not add a credit field.
- `contas/views.py` — `area` renders trial or paid quota. Add the activate POST. Do not decrement on GET.
- `contas/templates/contas/area.html` — trial copy stays. Paid state shows the plan, the monthly remainder, and Resultados when the month is empty. Padrão and Plus are POST buttons. Personalizado is contact text only.
- `contas/migrations/0003_cota_gratis.py` — latest migration. Add `0004` for the three columns only. No new `ENABLE`/`FORCE`.
- `contas/tests/test_isolamento.py` — raw `INSERT` omits newer columns. Keep that insert working.
- `contas/tests/test_cota.py` — free-trial cases must keep passing.
- `config/urls.py` — add the activate path under the area.
- `README.md` — say activation stores the plan and does not call a gateway.
- `sprint-status.yaml` — set `1-5-usar-o-grátis-e-ver-o-bloqueio` to `done` and `1-6-ativar-plano-pago` to `review` when the code is finished.
- `deferred-work.md` — keep the signup race entry. A payment provider is not deferred work; the architecture forbids one until a later decision names it.
- `MVP/`, `_bmad/`, `.agents/`, planning artifacts — do not change.

## Tasks & Acceptance

**Execution:**
- [x] `contas/models.py`, `contas/migrations/0004_plano_pago.py` -- plan and monthly counter on `contas_conta` -- the existing policy has to cover them
- [x] `contas/cota.py`, `contas/views.py`, `contas/templates/contas/area.html`, `config/urls.py` -- activate Padrão or Plus and keep the free gate -- Personalizado must not write, and no gateway is called
- [x] `contas/tests/test_plano.py`, `contas/tests/test_isolamento.py` -- matrix on SQLite, plan isolation on Postgres -- default `uv run pytest` still needs no Postgres
- [x] `README.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml` -- no-gateway note, 1.5 `done`, 1.6 `review`

**Acceptance Criteria:**
- Given an authenticated account, when it activates Padrão, then `contas` stores the plan and 30 searches for the America/Sao_Paulo calendar month, and no module calls Mercado Pago, Stripe, or another gateway.
- Given an authenticated account, when it activates Plus, then the month quota becomes 100 searches, and monitoring gates match Padrão.
- Given Personalizado, when the account consults it, then the product asks for contact and does not store a quota or activate the plan.
- Given an active paid plan, when the calendar month turns, then the quota restarts at 30 or 100 for that plan, and the previous month's remainder does not accumulate.
- Given a paid plan with the month quota at zero and no credit, when the account enters, then it sees already saved results, and a new search is not accepted.

## Implementation Notes

Activation writes `plano` only. The first time `plano` was empty it also sets `pesquisas_mes_usadas` to 0 and `mes_da_cota` to the first day of the current America/Sao_Paulo month. A later switch in the same month changes `plano` and leaves the used count. A different month does not rewrite the stored count until the next accepted search; remaining searches ignore that stored count and the accepted search then stores 1 for the new month. Personalizado is contact text. `POST /area/plano/` with `plano=personalizado` renders the area and does not save.

## Spec Change Log

## Review Triage Log

## Design Notes

Activation does not charge. The architecture says no gateway until a later decision names one. Rafael does not need to provide payment keys for this story.

`resultados_gravados` returns an empty list, the same way `nomes_de_radar` does. The blocked paid area can list results when a later epic stores them.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass on SQLite, plan isolation skipped
- `uv run pytest --ds config.postgres_settings` -- expected: pass, including plan isolation, against PostgreSQL
- `uv run python -c "import django; print(django.get_version())"` -- expected: `6.1.1`
