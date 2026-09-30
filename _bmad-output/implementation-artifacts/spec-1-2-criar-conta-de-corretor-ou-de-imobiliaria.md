---
title: 'Criar conta de corretor ou de imobiliária'
type: 'feature'
created: '2026-09-29'
status: 'done'
route: 'dispatch'
baseline_commit: 'fcc7a72324fb357950f5adae08988dd9476db347'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A visitor who is a CRECI broker or a legal-entity brokerage cannot create an account, so nobody can enter the client area.

**Approach:** Add one signup on the public site. The visitor chooses corretor or imobiliária, the server checks CRECI or CNPJ by format, and success opens the same client area for both.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1, PostgreSQL in `config.settings`. `contas.Conta` is `AUTH_USER_MODEL` with a UUID primary key and email as the login identifier, migrated before any other app table. Signup is `GET`/`POST /criar-conta/`. Success stores a hashed password, opens a session, and redirects to `/area/`, whose heading is "Área do cliente" and whose template is shared. CRECI is digits, an optional `F` or `J`, and one of the 27 Brazilian UFs; separators are optional. CNPJ is 14 digits with the official check digits after punctuation is removed; all-identical digits fail. No council or Receita lookup. Email is unique after lowercasing. Passwords use Django's validators, minimum 8 characters. Name, phone, razão social, and responsável are required only for the chosen type and must be non-blank after strip. Pages use the existing light base. Pytest uses an in-memory SQLite overlay; the application engine stays PostgreSQL.

**Never:** Do not add login, logout, or password recovery, and do not change anonymous `/entrar/` (story 1.3). Do not enable row-level security, `set_config`, or database roles (story 1.4). Do not record plans, quota, credits, or a trial gate (stories 1.5–1.7). Do not add social login, SSO, multiple roles, Celery, Redis, a payment gateway, or a second frontend. Do not make CRECI or CNPJ unique. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Corretor signup | `POST /criar-conta/` tipo `corretor`, nome `Ana Lima`, email `ana@exemplo.com`, telefone `11987654321`, senha `senha-segura`, CRECI `123456-SP` | One physical-person row, hashed password, session, redirect to `/area/`. Heading "Área do cliente" and the name Ana Lima. | N/A |
| Imobiliária signup | tipo `imobiliaria`, razão social `Casa ABCD Ltda`, CNPJ `11.222.333/0001-81`, responsável `Bruno`, email `casa@exemplo.com`, telefone `1133334444`, senha `senha-segura` | One legal-entity row. Same `/area/` template and heading, showing Casa ABCD Ltda. | N/A |
| CRECI without UF | tipo `corretor`, CRECI `123456`, other corretor fields valid | No row. CRECI is indicated with "Informe o CRECI no formato número e UF." | Re-render the form. |
| Invalid CNPJ | tipo `imobiliaria`, CNPJ `11222333000182`, other imobiliária fields valid | No row. CNPJ is indicated with "Informe um CNPJ com 14 dígitos e dígitos verificadores válidos." | Re-render the form. |
| Missing type | No `tipo` | No row. Tipo is indicated with "Escolha corretor ou imobiliária." | Re-render the form. |
| Email already used | `ana@exemplo.com` exists; post uses `Ana@exemplo.com` | No second row. Email is indicated with "Este e-mail já está em uso." | Re-render the form. |
| Portal entry | Anonymous `GET /` | "Criar conta" links to `/criar-conta/`. The Área do cliente link stays `/entrar/`. | N/A |
| Closed area | Anonymous `GET /area/` | No account data and no session. Redirect to `/entrar/`. | N/A |

</frozen-after-approval>

## Code Map

- `contas/views.py`, `config/urls.py` — portal and `entrar` only. Add `/criar-conta/` and `/area/`. Leave `entrar` as a formless placeholder.
- `config/settings.py` — PostgreSQL via `database_from_url`. Add auth, contenttypes, sessions, `AUTH_USER_MODEL`, password validators, and middleware. Do not switch the engine.
- `config/test_settings.py` — new overlay: import production settings and set `DATABASES` to SQLite `:memory:`.
- `contas/tests/test_portal.py` — asserts Django 6.1.1 and the production engine. Read that engine from `config.settings`, not the overlay.
- `contas/templates/contas/portal.html` — keep `<a href="/entrar/">Área do cliente</a>`. Add the signup link.
- `contas/templates/contas/base.html`, `contas/static/contas/portal.css` — reuse. No hex colors.
- `contas/models.py` — missing. Add `Conta` here.
- `spec-1-1-ver-produtos-e-planos-no-portal.md` — done. Do not reopen it.
- `sprint-status.yaml` — key `1-1-ver-produtos-e-planos-no-portal` is `review` in yaml and `done` in the spec; set `done`. Set `1-2-criar-conta-de-corretor-ou-de-imobiliária` to `review` when the code is finished.
- `MVP/`, `_bmad/`, `.agents/`, planning artifacts — do not change.

## Tasks & Acceptance

**Execution:**
- [x] `contas/models.py`, `contas/migrations/0001_initial.py` -- add `Conta` and the initial migration -- story 1.4 attaches RLS to this table later
- [x] `contas/forms.py`, `contas/views.py`, `contas/templates/contas/criar_conta.html`, `contas/templates/contas/area.html`, `contas/templates/contas/portal.html`, `config/urls.py` -- signup, the matrix messages, the session, and the shared area -- this is what the visitor does
- [x] `config/settings.py`, `config/test_settings.py`, `pyproject.toml` -- wire auth and point pytest at `config.test_settings` -- tests must not need a local PostgreSQL server
- [x] `contas/tests/test_criar_conta.py`, `contas/tests/test_portal.py` -- cover the matrix and keep the production-engine assertion -- acceptance runs without Postgres
- [x] `README.md` -- local PostgreSQL setup and how to run the tests -- the app stays on PostgreSQL
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- mark 1.1 `done` and 1.2 `review` -- 1.1 is already implemented

**Acceptance Criteria:**
- Given the public portal, when a visitor submits a corretor signup with nome, email, telefone, senha, and a CRECI of number plus UF, then one physical-person account is created, CRECI is checked only by format, and the visitor enters `/area/`.
- Given the public portal, when a visitor submits an imobiliária signup with razão social, a valid 14-digit CNPJ, responsável, email, telefone, and senha, then one legal-entity account is created and `/area/` uses the same template as the corretor.
- Given a CRECI without UF, a CNPJ with an invalid check digit, a missing type, or an email already used, when the visitor submits the form, then no account is created and the invalid field is indicated.

## Implementation Notes

- `Conta` stores CRECI in a canonical form (`123456-SP` or `123456-F-SP`) and CNPJ as 14 digits. The check is local; nothing calls the council or Receita.
- Pytest uses `config.test_settings` (SQLite in memory). `config.settings` still configures PostgreSQL.
- Signup calls `login` so the visitor enters `/area/`. `/entrar/` is unchanged. RLS is not enabled.

## Spec Change Log

## Review Triage Log

- medium — `contas/forms.py` email field uses Django's 320-character default while `Conta.email` is 254. PostgreSQL raises `DataError` and `criar_conta` does not catch it. Patch.
- low — Canonical CRECI can exceed the 64-character column when hyphens are inserted. Rejected: a 62-digit CRECI is not everyday input, and the fix adds a length branch.
- false — A dotted number such as `123.456-SP` is rejected. The spec allows separators between the number, the optional F/J, and the UF, not dots inside the number. The specified format message is correct.
- false — Django's password validators ignore `nome`, accept eight spaces, and there is no confirmation field. The spec requires those validators and a single senha. Password recovery belongs to story 1.3.
- low — An over-long unused field blocks the chosen type. Rejected: exceeding the unused field's max length is not everyday use, and ignoring those errors adds a branch.
- medium — `README.md` tells Debian/Ubuntu to use `postgresql://localhost/rondimob`, which opens TCP and fails a default peer-auth install. Homebrew `postgresql@18` is keg-only, so `createdb` is not on `PATH`. Patch.
- false — Contrib tables can migrate before `Conta`. No other product app exists, and `contas.0001` depends on nothing, so it does not wait on one. Framework tables are not the architecture's app tables.
- false — The area has no return link, `/entrar/` ignores a session, and a second signup switches accounts. The spec freezes `/entrar/` and the portal link. Story 1.3 owns the later session. A new email is a new account.
- medium — `test_short_password_does_not_create_a_row` treats a body containing `8` as proof of the length validator. The charset, the phone, and the other validators already satisfy that. Patch with the validator tests below.
- false — `AbstractBaseUser.is_active` is the class value `True`, and the model does not cross-check type columns. Authentication works. Deactivation and extra database checks are outside this story. The form is the only writer.
- low — A required field of only Unicode format characters passes `strip()`. Rejected: that input is not everyday, and filtering categories adds a guard.
- medium — Password validators are not pinned. Pre-verified: removing any one validator, or lowering the minimum length, still passes the short-password test. Patch.
- medium — The `IntegrityError` duplicate-email branch never runs in tests. Pre-verified: `clean_email` already returns the message, so deleting the `except` still passes. Defer: the sequential duplicate is asserted, and the branch is only the insert race.
- medium — Signup CSRF is not checked. Pre-verified: the test client does not enforce CSRF, so removing the middleware still passes. Patch.
- medium — `GET /criar-conta/` does not assert the form controls. Pre-verified: deleting the email and senha widgets still passes the POST tests. Patch.
- low — The similarity error says "email" because the field has no Portuguese verbose name. Direct correction: `verbose_name` "e-mail". Patch.

## Design Notes

Type-specific columns stay blank for the other type. The auth session is how signup enters the area. Story 1.3 owns `/entrar/`, logout, and password recovery. Story 1.4 owns `FORCE ROW LEVEL SECURITY` on this table.

CRECI that passes: `123456-SP`, `123456/SP`, `123456FSP`, `123456-F/SP`. CRECI that fails: `123456`, `SP`, `123456-XX`. CNPJ `11222333000181` and `11.222.333/0001-81` pass. `11222333000182` and `00000000000000` fail.

## Verification

**Commands:**
- `uv run pytest` -- expected: all tests pass without a local PostgreSQL server
- `uv run python -c "import django; print(django.get_version())"` -- expected: `6.1.1`
