---
title: 'Uma conta não lê a outra'
type: 'feature'
created: '2026-09-30'
status: 'done'
route: 'dispatch'
baseline_commit: '9668734d0b4a37bac89e37f84e0e56e559e158af'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Two accounts share one `contas_conta` table, and a query can still return the other account's row. Story 1.2 left that table ready for row-level security and did not turn it on.

**Approach:** Turn on `ENABLE` and `FORCE ROW LEVEL SECURITY` for `contas_conta` only. Web and worker connect as roles that are not superuser, not the table owner, and not `BYPASSRLS`. Each private transaction calls `set_config('app.conta_id', ..., true)` before the queries. The setting ends with the transaction. One schema, no django-tenants.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1, PostgreSQL in `config.settings`. Policy name `conta_isola` on `public.contas_conta` only. `USING` matches `id::text = current_setting('app.conta_id', true)` or, for login before the id is known, `email = current_setting('app.login_email', true)` when that setting is non-empty. `WITH CHECK` is only `id::text = current_setting('app.conta_id', true)`. Both settings are transaction-local (`true`). Roles `rondimob_web` and `rondimob_worker` are `LOGIN`, `NOSUPERUSER`, `NOBYPASSRLS`, and not the owner of `contas_conta`. Migrate stays on the owner URL. The web process uses `rondimob_web`; the Celery worker uses `rondimob_worker`. Dev passwords are `dev-only-web` and `dev-only-worker`. Middleware after the session and before auth opens one `transaction.atomic` and sets `app.conta_id` from `_auth_user_id` (empty when absent). Signup sets `app.conta_id` to the new UUID before insert. Login sets `app.login_email` before `authenticate`. The reset view and the recovery task set `app.conta_id` before loading that account. On SQLite the helper does nothing so the current suite still runs. Postgres tests connect as the web and worker roles and prove the matrix. No django-tenants.

**Never:** Do not add policies to radar, favorito, alerta, crédito, visto, or envio (they do not exist). Do not add plans, quota, credits, or a trial gate (stories 1.5–1.7). Do not give the web or worker role `BYPASSRLS`, superuser, or ownership of `contas_conta`. Do not use a session-level `SET` that survives the transaction. Do not change signup field rules or the recovery email boundary. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts. Do not delete the existing `deferred-work.md` entry.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Read and update as A | Two `Conta` rows. Web role, one transaction, `set_config('app.conta_id', A, true)` | `SELECT` returns only A. Updating A's name persists. Updating B changes no row. | N/A |
| Setting dies | Same connection. Commit, then a new transaction with no `set_config`. Then a transaction for B. | The empty transaction returns no `contas_conta` row. B's transaction returns only B. | N/A |
| Roles and policy | After migrate | `rondimob_web` and `rondimob_worker` are not superuser, not `BYPASSRLS`, and not the owner. `contas_conta` has `ENABLE` and `FORCE`. The only RLS relation in `public` is `contas_conta`. `django_tenants` is not installed. | N/A |
| Login lookup | Web role, `app.login_email` set to A's email, `app.conta_id` empty | The query returns A and not B. | N/A |
| SQLite suite | `uv run pytest` on `config.test_settings` | Existing tests pass. The helper does not call `set_config`. Isolation tests skip. | N/A |

</frozen-after-approval>

## Code Map

- `contas/models.py` — `Conta` UUID pk and `ContaManager.create_user`. Set the new id and `app.conta_id` before `save` on PostgreSQL. Do not add a second account table.
- `contas/views.py` — `entrar` calls `authenticate` with no tenant context. Set `app.login_email` first. `definir_senha` loads by uid. Set `app.conta_id` from that uid first. Leave signup validation as it is.
- `contas/tasks.py` — `preparar_link_de_recuperacao` loads `Conta` by id. Set `app.conta_id` inside `transaction.atomic` before the get.
- `config/settings.py` — PostgreSQL via `database_from_url`, auth middleware, `CELERY_BROKER_URL`. Add the RLS middleware between session and auth. Choose owner, web, or worker URL from the command: migrate and makemigrations use the owner; celery uses the worker; otherwise web.
- `config/test_settings.py` — SQLite overlay. Keep it. Do not point the default pytest run at Postgres.
- `contas/migrations/0001_initial.py` — creates `contas_conta` as the migrate user, who remains the owner. Add `0002` for roles, grants, and the policy. Skip the SQL when the vendor is not PostgreSQL.
- `contas/tests/test_criar_conta.py`, `contas/tests/test_sessao.py` — must keep passing on SQLite.
- `README.md` — Postgres install, the two roles, and the two pytest commands.
- `sprint-status.yaml` — set `1-3-entrar-sair-e-recuperar-a-senha` to `done` and `1-4-uma-conta-não-lê-a-outra` to `review` when the code is finished.
- `deferred-work.md` — keep the signup race entry.
- `MVP/`, `_bmad/`, `.agents/`, planning artifacts — do not change.

## Tasks & Acceptance

**Execution:**
- [x] `contas/isolamento.py`, `contas/middleware.py`, `contas/models.py`, `contas/views.py`, `contas/tasks.py`, `config/settings.py` -- transaction-local `set_config` around private reads and writes -- the setting has to exist before the query and die with the transaction
- [x] `contas/migrations/0002_isolamento_da_conta.py` -- roles, `ENABLE`/`FORCE`, policy `conta_isola`, grants -- only `contas_conta` is private in this story
- [x] `contas/tests/test_isolamento.py`, `pyproject.toml` -- Postgres tests for the matrix, skipped on SQLite -- default `uv run pytest` still needs no Postgres
- [x] `README.md` -- owner, web, and worker URLs, plus both test commands -- say what SQLite covers and what needs Postgres
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- mark 1.3 `done` and 1.4 `review` -- 1.3 is already merged

**Acceptance Criteria:**
- Given two accounts, when A opens a transaction, then A reads and updates only A's row and the query does not return B.
- Given a private account read, when the transaction starts, then the code calls `set_config('app.conta_id', ..., true)` before the queries and the value does not leak into the next transaction.
- Given the web and worker roles, when they connect, then they are not superuser, not owners of the private table, and not `BYPASSRLS`, and `contas_conta` has `ENABLE` and `FORCE ROW LEVEL SECURITY` in one schema without django-tenants.
- Given radar, favorito, alerta, crédito, visto, and envio do not exist, when this story ends, then only the account table has the policy.

## Implementation Notes

Signup and password recovery look up an account by email before the id is known. Those reads set `app.login_email` in the same transaction, using the same policy branch as login. `WITH CHECK` still requires `app.conta_id`. `DATABASE_URL`, when set, replaces the command-selected role URL. Portal page tests use `TestCase` because the isolation middleware opens a transaction on every request.

## Spec Change Log

## Review Triage Log

- `high` — `contas/migrations/0002_isolamento_da_conta.py` — `manage.py runserver` as `rondimob_web` raises `ProgrammingError: permission denied for table django_migrations` inside `check_migrations`. Route: patch.
- `false` — `0002` `CREATE ROLE` inside the default migration transaction — PostgreSQL 16.15 accepted `BEGIN; CREATE ROLE; ROLLBACK` and `migrate` applied `0002`.
- `low` — session `app.conta_id` plus `app.login_email` can make an unfiltered `SELECT` return two rows — current views filter by email or primary key, and no request lists every account. Rejected: clearing the setting adds a branch users do not hit.
- `low` — Django's test client uses the owner connection — the matrix is executed on `rondimob_web` and `rondimob_worker` connections, and a web-role client signed up, logged in, and opened `/area/`. Rejected: pointing the test client at the web role needs a second database alias.
- `low` — `_apagar` deletes as the owner with no `set_config` — the documented owner is a superuser, which bypasses `FORCE`. Rejected.
- `false` — migrate rewrites the dev passwords, the email branch can read the password hash, and reverse leaves the roles — the spec fixes those passwords, login must read the row to check the password, and cluster roles stay.
- `low` — README does not mention `pg_hba.conf` — the Ubuntu defaults authenticated `rondimob_web` over `127.0.0.1` and signup returned 302. Rejected.
- `false` — `definir_conta` does not open a transaction — the middleware, `Conta.save`, and the recovery task already hold one; web-role signup inserted the row.
- `false` — worker DML and web access to every `django_session` row — the spec grants that DML, and `django_session` is not a private account table in this story.
- `false` — no CI job runs the Postgres suite — the spec's verification command is the documented pytest invocation, and it was run.
- `medium` — `USING` also admits `DELETE` when `app.login_email` matches — real for a raw `DELETE`, and no view deletes. Rejected: restricting the command would change the approved `conta_isola` expression.
- `low` — `app.login_email` stays set after the lookup — the same request does not issue a second unfiltered query. Rejected.
- `false` — `python -m celery` would use the web URL — `database_url_for_argv(["python", "-m", "celery", "worker"])` already expects the worker URL.
- `false` — an explicit `DATABASE_URL` can be a superuser — the README states that this replaces the role on purpose.
- `low` — a session-hash mismatch leaves `app.conta_id` set while `request.user` is anonymous — views in that request use `request.user`. Rejected.
- `false` — `ALTER ROLE` resets an existing `rondimob_web` — the spec requires those attributes and the dev password.
- `false` — the rejected cross-account insert leaks a row — `conn.transaction()` rolls it back.
- `false` — the email branch returns B during A's transaction — a transaction that only sets A's id returns only A; the email branch is the approved login lookup.
- `medium` — order assertions run inside `TestCase`, so dropping the middleware transaction still passes — `set_config(..., true)` would die before the query under autocommit. Route: patch.

## Design Notes

`FORCE` applies to the table owner, but a superuser still bypasses it. That is why migrate uses the owner URL and the app must not. Login cannot know the UUID yet, so the same transaction may set `app.login_email` to the submitted address. The policy then returns that one row. An empty setting matches nothing.

Dev URLs: owner `postgresql:///rondimob` (peer), web `postgresql://rondimob_web:dev-only-web@127.0.0.1/rondimob`, worker `postgresql://rondimob_worker:dev-only-worker@127.0.0.1/rondimob`. Grant the web role `django_session` as well, or login cannot store a session. Do not grant `BYPASSRLS`.

SQLite `uv run pytest` proves the pages and skips isolation. `uv run pytest --ds config.postgres_settings` proves the policy. The cloud run must execute the second command against a real server.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass on SQLite, isolation tests skipped, no Postgres required
- `uv run pytest --ds config.postgres_settings` -- expected: pass, including isolation, against PostgreSQL
- `uv run python -c "import django; print(django.get_version())"` -- expected: `6.1.1`
