---
title: 'Ver produtos e planos no portal'
type: 'feature'
created: '2026-09-29'
status: 'done'
route: 'dispatch'
baseline_commit: 'NO_VCS'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A visitor cannot see what rondimob does or what it costs, because the Django app does not exist yet.

**Approach:** Create the Django project and one public page, in Portuguese, that shows the products, the four plans, the credit pack, and a visible client-area entry. The page does not require an account.

## Boundaries & Constraints

**Always:** Python 3.13.15, Django 6.1.1, PostgreSQL 18.6 as the configured database engine. App folders `config` and `contas` live at the repository root. The public page and the client-area entry are the same site. Prices are fixed: Grátis R$ 0 with 10 searches in 14 days; Padrão R$ 97 per month with 30 searches; Plus R$ 197 per month with 100 searches; Personalizado is sob consulta; the pack is R$ 47 for 10 searches. The visual base is light, in the usual real-estate SaaS pattern, and is not a dark theme. The concrete palette stays with UX. Copy states that the product monitors prices by region and competing brokerages in the ABCD, in one place.

**Never:** Do not add signup, login, session, RLS, plans-as-data, credits, radars, scraping, Celery, Redis, a payment gateway, or a second frontend app. Do not edit `MVP/`, `_bmad/`, `.agents/`, or planning artifacts. Do not choose hex colors as a product decision.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Public portal | Anonymous GET `/` | Products, four plans, credit pack, and the prices above are visible. No account is required. | Unknown paths return the framework 404. |
| Client-area entry | Anonymous visitor on `/` | A link named Área do cliente points to `/entrar/`. | The link is present without a session. |
| Entry destination | Anonymous GET `/entrar/` | A light page confirms the client area is on this site and that access will ask for email and password. It does not authenticate. | No login form and no account check. |
| Light base | Either public page | Background is light. No dark theme is applied. | N/A |

</frozen-after-approval>

## Code Map

- Repository root — no `manage.py`, `config/`, or `contas/` yet. This story creates them.
- `_bmad-output/implementation-artifacts/epic-1-context.md` — epic constraints. Read it. Do not restate it into new product rules.
- `_bmad-output/planning-artifacts/epics.md` Story 1.1 — source of the acceptance criteria already copied above.
- `MVP/mvp.md` — old sketch. Do not implement from it and do not modify it.
- `_bmad/`, `.agents/`, `_bmad-output/planning-artifacts/` — leave unchanged.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml` -- pin Python 3.13.15 and Django 6.1.1, with psycopg, and a pytest-django test runner -- the app has no dependency file yet
- [x] `manage.py`, `config/settings.py`, `config/urls.py`, `config/wsgi.py` -- create the project; set `DATABASES` to PostgreSQL 18 via `DATABASE_URL`, defaulting to a local database named `rondimob` -- the story requires that engine even though this page does not query it
- [x] `contas/` -- add the app, the `/` and `/entrar/` views, Portuguese templates, and one light stylesheet -- this is the public surface
- [x] `contas/tests/test_portal.py` -- cover the I/O matrix with Django `SimpleTestCase` so the test does not need a running Postgres -- the page must be checkable without a live database

**Acceptance Criteria:**
- Given the new project, when Django reports its version and the database engine, then Django is 6.1.1 and the engine is PostgreSQL.
- Given an anonymous visitor, when they open `/`, then they see the products, the four plans, the credit pack, and the prices in the Intent, and the page does not require an account.
- Given the same site, when they look for the client area, then they find Área do cliente linking to `/entrar/`, and that page does not authenticate.
- Given either page, when it renders, then the base is light and no dark theme is applied.

## Implementation Notes

- Django 6.1.1 on Python 3.13.15. Public pages do not query the database. `manage.py test contas.tests.test_portal` passed 6 tests.
- No git repository, so there is no commit baseline. Review used the new project files directly.
- `runserver` was not confirmed against a live Postgres. The local default `postgresql://localhost/rondimob` has no server yet.

## Spec Change Log

## Review Triage Log

- false — Python and Django pins reject other patches. The spec requires Python 3.13.15 and Django 6.1.1, and the version assertion matches that.
- low — `database_from_url` drops URL query parameters such as `sslmode`. The default URL has none, and parsing every option is more than a direct correction. Rejected.
- low — An empty database path is accepted. Raising on it adds a guard the public page does not reach. Rejected.
- low — A trailing slash stays in the database name (`config/settings.py` `database_from_url`). Direct strip. Patch.
- low — `DJANGO_ALLOWED_HOSTS` is not stripped, so a padded host will not match. Direct strip. Patch.
- low — `testserver` is in the default allow list. The test client needs it, and removing it is a guard. Rejected.
- low — Dev secret and `DEBUG` default true, with no `.env.example`. Those defaults are how this local page runs. Hardening adds guards. Rejected.
- low — The 404 test requires Django's English debug sentence, so `DEBUG=false` fails it. The matrix only requires the framework 404 status. Direct test change. Patch.
- false — `/entrar/` has no link back, the portal href is literal, and Personalizado has no mail link. The matrix asks for the words and the `/entrar/` link, and both are present. "por mês" is on the price line.
- low — The stylesheet test rejects any `#`. That keeps the no-hex decision, and loosening it is not a user-facing fix. Rejected.
- false — `find("contas/portal.css")` without an assert fails loudly if the file is missing. That is the right signal.
- low — The portal title and h1 are not asserted. The heading is in the template, and extra assertions are not a correction of a broken page. Rejected.
- medium — `test_django_version_and_postgresql_engine` never checks user, password, port, percent-encoding, or a non-default `DATABASE_URL`. A parser that ignores `DATABASE_URL` still passes. Pre-verified verification gap. Patch.
- low — `STATIC_ROOT` is unset. With `DEBUG` true, `staticfiles` serves the sheet. A production static pipeline is more than this page. Rejected.
- low — `POST /entrar/` returns 200 and CSRF middleware is absent. There is no form. `require_GET` would add a guard. Rejected.
- false — `STATIC_URL = "static/"` was claimed to stay relative. Django prefixes a slash, and the rendered href is `/static/contas/portal.css`.
- low — A bad database port aborts import with `ValueError`. That loud failure is correct. Rejected.
- low — An empty `DJANGO_ALLOWED_HOSTS` replaces the default with an empty list. Treating blank as the default is direct. Patch.
- low — An allow-list entry that includes a port will not match. The default has no port, and stripping ports adds a branch. Rejected.
- low — A padded `DJANGO_DEBUG` is treated as false. Direct strip. Patch.
- false — An empty `DJANGO_SECRET_KEY` was claimed to sign with an empty key. Django raises `ImproperlyConfigured` when the key is empty.

## Design Notes

Use Django templates and one stylesheet. Do not add a JavaScript frontend. Keep the palette to neutral light surfaces and dark text only, so a later UX pass can replace the tones without changing the markup contract. The client-area URL exists so the entry does not 404; story 1.3 replaces it with the real login.

## Verification

**Commands:**
- `uv run --python 3.13.15 python -c "import django; print(django.get_version())"` -- expected: `6.1.1`
- `uv run --python 3.13.15 python manage.py test contas.tests.test_portal` -- expected: all tests pass
