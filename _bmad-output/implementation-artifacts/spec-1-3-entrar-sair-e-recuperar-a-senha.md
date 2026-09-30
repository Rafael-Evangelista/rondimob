---
title: 'Entrar, sair e recuperar a senha'
type: 'feature'
created: '2026-09-30'
status: 'done'
route: 'dispatch'
baseline_commit: '26e5fcf07c06563be9b1d4af75bd6b6de6b87805'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After signup, a person cannot sign in again, sign out, or replace a forgotten password. `/entrar/` is still a placeholder with no form.

**Approach:** Replace `/entrar/` with email and password. A correct login opens `/area/` and stays until logout. A wrong login opens nothing. Password recovery only enqueues a Celery task; the worker logs the link and does not call an email provider. The link sets a new password and the old one stops working.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1, PostgreSQL in `config.settings`. Login is `GET`/`POST /entrar/` with email and password. Success redirects to `/area/` and the session survives another request until `POST /sair/`. Logout redirects to `/entrar/`, and the old session cookie does not authenticate anyone. Wrong email or wrong password responds with "E-mail ou senha incorretos." and does not set a session. `GET /area/` without a session still redirects to `/entrar/`. Recovery is `GET`/`POST /recuperar-senha/`. The view calls `contas.tasks.preparar_link_de_recuperacao.delay` and does not build the link or send mail. An unknown email gets the same confirmation and enqueues nothing. The worker is Celery 5.6.3 with broker `redis://localhost:6379/0`. The task logs `/recuperar-senha/<uidb64>/<token>/` to stdout. That page sets a new password with the existing validators, minimum 8 characters. The old password then fails. Pages stay on the light base. Pytest mocks `delay` and calls the task function itself, so it needs neither Redis nor PostgreSQL.

**Never:** Do not choose an email provider or send mail. Do not run token generation inside the login request. Do not enable row-level security, `set_config`, or database roles (story 1.4). Do not record plans, quota, credits, or a trial gate (stories 1.5–1.7). Do not add social login, SSO, or multiple roles. Do not change signup rules. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts. Do not delete the existing `deferred-work.md` entry.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Login | Existing `Conta`, `POST /entrar/` with its email and password | 302 to `/area/`, session cookie, heading "Área do cliente", that account's name. A later `GET /area/` with the same session is still that account. | N/A |
| Logout | That session, `POST /sair/` | 302 to `/entrar/`. `GET /area/` redirects to `/entrar/`. Replaying the old session cookie does not open this account or another account. | `GET /sair/` does not log out. |
| Bad credentials | Wrong email, or right email and wrong password | 200, "E-mail ou senha incorretos.", no session. `GET /area/` redirects to `/entrar/`. | Re-render the login form. |
| Recovery request | `POST /recuperar-senha/` with the account email | The response has no token. `delay` is called once with that account id. The password is unchanged in this request. | Unknown email: same confirmation, `delay` is not called. |
| Recovery link | The path the task logs, `POST` with senha `nova-senha-8` | The password becomes `nova-senha-8`. The old password fails. The new one opens `/area/`. | A used or bad token shows "Este link não vale mais." and does not change the password. |

</frozen-after-approval>

## Code Map

- `contas/views.py` — `entrar` renders `contas/entrar.html` with no form (`contas/views.py` `entrar`). Replace it with login. `area` already redirects anonymous users to `entrar` and renders `contas/area.html`. Add logout and recovery. Leave `criar_conta` logging the new account in.
- `config/urls.py` — `/`, `/criar-conta/`, `/area/`, `/entrar/`. Add `/sair/` and `/recuperar-senha/`.
- `contas/templates/contas/entrar.html` — placeholder copy and no form. Replace with the login form. Keep the light base from `contas/templates/contas/base.html`.
- `contas/templates/contas/area.html` — heading and `conta.nome_exibicao`. Add the logout form. Do not add a second client area.
- `contas/templates/contas/portal.html` — keep `<a href="/entrar/">Área do cliente</a>` and the signup link.
- `contas/models.py` — `Conta`, email login, `normalizar_email`, `ContaManager.get_by_natural_key`. Reuse `authenticate` against this user. Do not add RLS columns.
- `contas/forms.py` — `CriarContaForm` and password validators. Add login, recovery request, and new-password forms. Reuse `validate_password`.
- `contas/tests/test_portal.py` — `test_entrar_confirms_client_area_without_authenticating` forbids any form on `/entrar/`. Update it so a login form is present and `GET` still does not authenticate. Keep the PostgreSQL assertion on `config.settings`.
- `config/settings.py` — auth, sessions, CSRF, `AUTH_USER_MODEL`, PostgreSQL. Add the Celery broker setting. Do not switch the engine.
- `config/test_settings.py` — SQLite overlay only. Do not point tests at Redis.
- `config/__init__.py` — empty. Load the Celery app here.
- `pyproject.toml` — Django 6.1.1 and pytest. Pin Celery 5.6.3.
- `README.md` — local PostgreSQL and `uv run pytest`. Add Redis and the worker command. Tests still do not need those servers.
- `sprint-status.yaml` — set `1-2-criar-conta-de-corretor-ou-de-imobiliária` to `done` and `1-3-entrar-sair-e-recuperar-a-senha` to `review` when the code is finished.
- `deferred-work.md` — keep the signup race entry. Do not edit it.
- `MVP/`, `_bmad/`, `.agents/`, planning artifacts — do not change.

## Tasks & Acceptance

**Execution:**
- [x] `contas/forms.py`, `contas/views.py`, `contas/templates/contas/entrar.html`, `contas/templates/contas/area.html`, `contas/templates/contas/recuperar_senha.html`, `contas/templates/contas/definir_senha.html`, `config/urls.py` -- login, logout, and the recovery pages -- this is what the account does
- [x] `contas/tasks.py`, `config/celery.py`, `config/__init__.py`, `config/settings.py`, `pyproject.toml` -- Celery task that logs the link and is not called inline by the view -- the request must leave the HTTP cycle
- [x] `contas/tests/test_sessao.py`, `contas/tests/test_portal.py` -- cover the matrix, including a mocked `delay` and a direct task call -- pytest must not need Redis or PostgreSQL
- [x] `README.md` -- Redis, the worker command, and the existing pytest command -- the app stays on PostgreSQL and Celery
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- mark 1.2 `done` and 1.3 `review` -- 1.2 is already merged

**Acceptance Criteria:**
- Given an existing account, when the person submits the right email and password on `/entrar/`, then the session opens that account's `/area/` and stays until logout.
- Given an open session, when the account signs out, then `/area/` asks for login again and the old session does not open this account or another one.
- Given a wrong email or a wrong password, when the person tries to enter, then no session opens and `/area/` stays closed.
- Given an account that forgot the password, when they request recovery, then the request only enqueues a worker task and no email provider is called, and the logged link sets a new password that replaces the old one.

## Implementation Notes

- `POST /sair/` logs out. `GET /sair/` returns 405 and leaves the session in place.
- The recovery view only calls `delay`. The task prints the link and returns it. No email provider is called.
- Pytest uses SQLite, mocks `delay`, and calls the task function directly.

## Spec Change Log

## Review Triage Log

- low — `delay` is unguarded, so a down broker returns 500 for a known email and 200 for an unknown one. Rejected: with Redis running, as the README requires, the request does not hit this, and swallowing the error would hide a failed enqueue.
- false — Refreshing the confirmation POSTs again and older links stay valid until the password changes. A second POST is a second request. `PasswordResetTokenGenerator` invalidates every link when the hash changes, which the used-token test covers.
- low — The reset token stays on the URL, without `never_cache` or `sensitive_post_parameters`. Rejected: the spec's link is that URL, and the extra decorators are new guards.
- false — One password field, no help text, and a redirect to `/entrar/` after save. The matrix posts one `senha` and then logs in with it. A confirmation screen is not part of the story.
- medium — The worker logs a path with no host, and the README does not say how to open it or that the line is the only copy of the link. Patch the README.
- false — `CELERY_BROKER_URL` is the literal Redis URL from the spec. Pinning Redis 8.10.2 would fight the apt and Homebrew install the README already documents.
- false — The session cookie uses Django's 14-day default and is not marked Secure. Secure cookies break the local HTTP server. A second login replaces the browser session on purpose.
- low — Login and recovery have no throttle, and the password fields have no max length. Rejected: rate limiting is a new control this story does not ask for.
- low — Two overlapping posts of one live token can both pass `check_token`. Rejected: there is no second writer in normal use, and `select_for_update` is a new branch. The password that remains is the last save.
- low — `/entrar/` has no link to signup, and the email fields omit autocomplete. The signup link is everyday from the login page. Patch that link. Autocomplete is cosmetic and stays out.
- false — Empty fields already use Django's Portuguese required message under `LANGUAGE_CODE` `pt-br`. The account type does not change login.
- low — A missing account id in the worker, a Redis stall, or a deleted row during `set_password` can 500. Rejected: this story has no way to delete an account, and the fixes add guards for states the product does not reach.
- medium — Tests read `settings.CELERY_BROKER_URL` and mock `delay`, so deleting Celery config, autodiscover, or the Redis extra still passes. Pre-verified. Patch.
- medium — The new-password form has no `action`, and tests post the token URL themselves. A wrong action would still pass. Pre-verified. Patch.
- medium — CSRF tests only post without a token. Removing `{% csrf_token %}` still lets the default client succeed. Pre-verified. Patch.

## Design Notes

Django's `PasswordResetTokenGenerator` avoids a new table. The token dies after `set_password` because the hash changes. `GET /sair/` must not log out. The confirmation page uses the same text whether or not the email exists: "Se houver uma conta com esse e-mail, o pedido de nova senha foi registrado."

The task logs `recuperacao de senha conta=<uuid> link=/recuperar-senha/<uidb64>/<token>/`. Tests read that path from the task return value. They never connect to Redis.

## Verification

**Commands:**
- `uv run pytest` -- expected: all tests pass without a local PostgreSQL or Redis server
- `uv run python -c "import django; print(django.get_version())"` -- expected: `6.1.1`
