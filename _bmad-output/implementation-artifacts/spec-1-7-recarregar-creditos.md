---
title: 'Recarregar créditos'
type: 'feature'
created: '2026-09-30'
status: 'done'
route: 'dispatch'
baseline_commit: 'c9dca2bbb3dc480c77e9587a3cf80aeff4df63f8'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A paid account that finishes the month cannot buy 10 more searches, and a free account is not told to activate a plan first.

**Approach:** Store credit on the account, not on the plan. Reload is a web-request state change. Spend the month quota first. Credit accumulates and is spent only after that quota is zero.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1. One reload adds 10 searches at a recorded price of R$ 47 and does not change `plano`. Balance is the sum of remaining units. Another reload adds 10 more. Credit does not expire and does not reset when the month turns or the plan switches. While the America/Sao_Paulo month still has quota, an accepted search spends the month and leaves the balance. When that quota is already zero, the next accepted search decreases the balance by 1 and leaves the month counter at the cap. A free account cannot reload and never spends credit: the area asks to activate a plan. With a paid plan, month at zero, and balance at zero, `/area/` still shows Resultados and a new search is refused. Favorite and alert stay allowed on a paid plan. `POST /area/credito/` reloads only for Padrão or Plus. `GET /area/` does not reload or spend. The credit table uses `ENABLE` and `FORCE ROW LEVEL SECURITY`, a UUID id, and a policy that reads only `app.conta_id`. Postgres proves account A cannot read account B's balance.

**Never:** Do not call Mercado Pago, Stripe, or any other gateway, and do not invent credentials or a fake charge. Do not implement Epic 2 or run a real search. Do not store credit on `contas_conta` or add a second policy there. Do not let the free trial buy credit. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts. Do not delete the existing `deferred-work.md` entry. Do not mark `epic-1-retrospective` done.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Reload | Padrão or Plus. `POST /area/credito/` | One row, remaining 10, price 47, plan unchanged. Area shows 10 créditos and R$ 47 por 10 pesquisas. No gateway module. | Anonymous POST redirects to `/entrar/`. |
| Second reload | Same account reloads again | Balance is 20. Plan and month counter stay. | N/A |
| Month first | Paid, month still open, balance 10 | Accepted search increments the month by 1. Balance stays 10. | N/A |
| Credit next | Paid, month at the cap, balance 10 | Month counter stays at the cap. Balance becomes 9. | N/A |
| Month turn | Balance 9, then the calendar month changes | Balance stays 9. The next accepted search spends the new month. | N/A |
| Free reload | No paid plan. `POST /area/credito/` | No row. Area says to activate a plan. No Recarregar submit. | Redirects to `/area/` without writing. |
| Empty | Paid, month at the cap, balance 0 | `aceitar_pesquisa` returns false. `/area/` shows Resultados. | N/A |
| Other account | PostgreSQL, web role, `app.conta_id` is A | Select returns A's credit only. Updating B changes no row. | N/A |
| SQLite | `uv run pytest` | Reload and spend tests pass. Credit isolation skips. | N/A |

</frozen-after-approval>

## Code Map

- `contas/models.py` — add `Credito`: UUID pk, FK to `Conta`, numeric `preco`, integer `restante`, `criado_em`. No balance column on `Conta`.
- `contas/cota.py` — `saldo_credito` and `recarregar_credito`. Inside `aceitar_pesquisa`, reuse `_gastar_mes` and `_gastar_gratis`. Decrement the oldest remaining credit only when `_gastar_mes` returns false. `pode_pesquisar` is true on a paid plan when the month remains or the balance is above zero.
- `contas/views.py` — `area` shows the balance. Resultados only when the paid month remainder and the balance are both 0. Add the reload POST.
- `contas/templates/contas/area.html` — paid state adds the balance and a Recarregar form. Open and blocked trials show "Ative um plano para recarregar." and no Recarregar control.
- `config/urls.py` — add `area/credito/` next to `area/plano/`.
- `contas/migrations/0004_plano_pago.py` — latest. Add `0005` for the table, DML grants to `rondimob_web` and `rondimob_worker`, and `ENABLE`/`FORCE` plus policy `conta_isola` on `contas_credito` only. Skip that SQL on SQLite. The migrate role owns the table.
- `contas/tests/test_isolamento.py` — `test_roles_policy_and_single_private_table` expects only `contas_conta`. Also expect forced RLS on `contas_credito`. Leave the `contas_conta` policy as it is. Raw inserts into `contas_conta` stay valid.
- `contas/tests/test_cota.py`, `contas/tests/test_plano.py` — keep passing, including an empty month with no credit.
- `README.md` — reload stores 10 searches at R$ 47, spends the month first, accumulates, and does not call a gateway. Real charging waits until a later decision names a provider.
- `sprint-status.yaml` — `1-6-ativar-plano-pago` `done`, `1-7-recarregar-créditos` `review`. Leave `epic-1` `in-progress` and `epic-1-retrospective` `optional`.
- `deferred-work.md` — keep the signup race entry. Do not add a payment-provider entry.
- `MVP/`, `_bmad/`, `.agents/`, planning artifacts — do not change.

## Tasks & Acceptance

**Execution:**
- [x] `contas/models.py`, `contas/migrations/0005_credito.py` -- credit table with UUID, price, and remaining count -- its RLS policy hides another account's balance
- [x] `contas/cota.py`, `contas/views.py`, `contas/templates/contas/area.html`, `config/urls.py` -- reload for Padrão or Plus and spend the month before credit -- a free account must not write, and no gateway is called
- [x] `contas/tests/test_credito.py`, `contas/tests/test_isolamento.py` -- matrix on SQLite, credit isolation on Postgres -- default `uv run pytest` still needs no Postgres
- [x] `README.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml` -- no-gateway note, 1.6 `done`, 1.7 `review`, retrospective left `optional`

**Acceptance Criteria:**
- Given a Padrão or Plus account, when it reloads one package, then the balance increases by 10, the plan stays the same, and the recorded price is R$ 47, with no gateway and no search execution.
- Given month quota still available and a credit balance above zero, when a search is accepted, then the month quota decreases by one and the credit balance stays the same.
- Given month quota at zero and a credit balance above zero, when a search is accepted, then the balance decreases by one, and bought credit does not reset when the month turns.
- Given a free account, when it tries to reload, then the balance does not change and the product asks to activate a plan.
- Given the credit table, when account A reads the balance, then it does not see account B's balance, and the table uses `ENABLE` and `FORCE ROW LEVEL SECURITY` with a UUID id.

## Implementation Notes

## Spec Change Log

## Review Triage Log

- `low` — the paid area hardcodes the price and the form action instead of the Python constants. The spec freezes both the copy and the path, and the plan prices are already written the same way in the template. Rejected: everyday use shows R$ 47 and `/area/credito/`, and threading new context is more than a direct correction.
- `low` — equal `criado_em` values would order packages by UUID, and the clock patch does not bind the field default. Sequential inserts still get a later timestamp, so the oldest row is spent. Rejected: a same-microsecond tie is not everyday use, and a sequence column adds surface.
- `low` — credit isolation does not also assert INSERT, DELETE, or the worker role. The policy `WITH CHECK` is `conta_id` equals `app.conta_id`, and the web-role test already shows A cannot read or update B. Rejected: more DML cases are extra tests, not a broken policy.
- `false` — a CSRF-less POST of the reload is not accepted in the browser. The form includes `csrf_token` and `CsrfViewMiddleware` is installed. The test client leaves CSRF off, as the other POST tests do.
- `medium` — a balance of 1 can render `1 créditos` and the suite still passes. Route: patch, assert `1 crédito` and the absence of `1 créditos` on `GET /area/`.
- `false` — a credit row left at `restante` 0 does not accept another search. `_gastar_credito` ignores `restante` of 0, the sum is 0, and the area shows Resultados when the month and the balance are both 0.
- `false` — showing `0 pesquisas restantes` next to a positive credit balance is the month remainder, not a blocked account. The spec shows those lines separately, and the exhausted-month test already spends credit.
- `false` — switching from Plus to Padrão after more than 30 uses spends credit next because the month remainder is already 0. That is the specified order. A guard against it would keep the balance while refusing a search the spec accepts.
- `false` — `saldo_credito` during `GET /area/` runs inside `IsolamentoDaContaMiddleware`, which sets `app.conta_id` before the view. Reload and accept also set it before they write.
- `low` — reload tests use a corretor only. The gate is `plano_pago`, not the account type. Rejected: an imobiliária on Padrão uses the same function, and a second type is extra coverage.
- `false` — a closed free trial does not spend a stored credit row. `aceitar_pesquisa` spends credit only when `plano_pago` is true. A free account uses `_gastar_gratis`, which does not write when the trial is closed.
- `medium` — the paid Recarregar form's `action` is not asserted, so a wrong target would still pass. Route: patch, assert `action="/area/credito/"` on the paid area.
- `medium` — `GET /area/credito/` is not asserted, so dropping `@require_POST` could store a package. Route: patch, expect 405 and no credit row.
- edge-case layer returned no findings.

## Design Notes

Each reload inserts one `Credito` row with `restante` 10 and `preco` 47.00. Balance is the sum. Spend the oldest row that still has units. The paid area always offers Recarregar. Reload does not charge. Rafael needs no payment keys until a later decision names a provider.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass on SQLite, credit isolation skipped
- `uv run pytest --ds config.postgres_settings` -- expected: pass, including credit isolation, against PostgreSQL
- `uv run python -c "import django; print(django.get_version())"` -- expected: `6.1.1`
