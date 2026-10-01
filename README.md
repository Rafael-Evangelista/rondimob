# rondimob

Public portal and client area. The application database is PostgreSQL. Python 3.13.15, Django 6.1.1, and Celery 5.6.3.

## Local PostgreSQL

Install PostgreSQL, create a database named `rondimob`, then run the app. For local peer authentication, set `DATABASE_URL` to `postgresql:///rondimob`.

Debian or Ubuntu:

```bash
sudo apt update
sudo apt install -y postgresql
sudo service postgresql start
sudo -u postgres createuser --superuser "$USER"
createdb rondimob
```

macOS with Homebrew:

```bash
brew install postgresql@18
brew services start postgresql@18
export PATH="$(brew --prefix postgresql@18)/bin:$PATH"
createdb rondimob
```

Then, from this repository. Leave `DATABASE_URL` unset so each command picks its role:

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

`migrate` and `makemigrations` connect as the table owner through the peer URL `postgresql:///rondimob`. That migration creates `rondimob_web` and `rondimob_worker`. Neither role is a superuser, neither owns `contas_conta`, and neither has `BYPASSRLS`. The web process uses `postgresql://rondimob_web:dev-only-web@127.0.0.1/rondimob`. Those passwords are for local development only. An explicit `DATABASE_URL` replaces the command choice for every process, so the web process would no longer be the web role.

Open `http://localhost:8000/`. Signup is at `http://localhost:8000/criar-conta/`.

A new account's area shows the free trial: 10 searches left, and the last open day. The creation date in America/Sao_Paulo is day 1, and the last open day is 13 days later. Signup, login, logout, the public portal, and opening the area do not spend a search. After 10 searches, or on the following calendar day, the area shows the four plans and the radar names that already exist.

One form at `/area/radares/novo/` creates a radar in the ABCD. The city has to be Santo André, São Bernardo do Campo, São Caetano do Sul, or Diadema. A second radar stays in the account's list. Creating a radar does not spend a search. An edit updates the same radar and does not spend a search. A city outside the ABCD leaves the stored city.

Activating Padrão or Plus stores that plan on the account and the searches used in the current America/Sao_Paulo calendar month. It does not call Mercado Pago, Stripe, or any other payment gateway. Personalizado asks for contact and does not store a plan or a quota. A new month starts the quota again at 30 or 100; leftover searches do not carry over. With the month at zero and no credit, the area shows saved results and a new search is refused.

A reload stores 10 searches on the account at a recorded price of R$ 47. It spends the month quota first. Another reload adds 10 more, so credit accumulates. Bought credit does not reset when the month turns or the plan changes. Reload does not call a payment gateway. Real charging waits until a later decision names a provider.

## Redis and the worker

Password recovery does not send mail. No email is sent. `POST /recuperar-senha/` enqueues a Celery task. The broker is `redis://localhost:6379/0`. The worker logs one line to stdout, a path with no host. That line is the only copy of the link, and it is the reset credential until the password changes. Open it on the same site: `http://localhost:8000` plus the path.

Debian or Ubuntu:

```bash
sudo apt update
sudo apt install -y redis-server
sudo service redis-server start
```

macOS with Homebrew:

```bash
brew install redis
brew services start redis
```

In another terminal, from this repository. The worker connects as `rondimob_worker` at `postgresql://rondimob_worker:dev-only-worker@127.0.0.1/rondimob`:

```bash
uv run celery -A config worker -Q celery,zap,viva-real,olx --loglevel=info
```

The ZAP task `coleta.tasks.coletar_zap` uses the queue `zap`. With no payload argument it reads `coleta/fixtures/zap-exemplo.json` and upserts that recorded listing. It does not call ZAP, Viva Real, OLX, or any other site. Live access waits until Rafael chooses how ZAP may be read.

The Viva Real task `coleta.tasks.coletar_viva_real` uses the queue `viva-real`. With no payload argument it reads `coleta/fixtures/viva-real-exemplo.json` and upserts that recorded listing. It does not call the site. A failure on one queue does not cancel the other. Live access waits until Rafael chooses how Viva Real may be read.

The OLX task `coleta.tasks.coletar_olx` uses the queue `olx`. With no payload argument it reads `coleta/fixtures/olx-exemplo.json` and upserts that recorded listing. It does not call the site. A failure on one queue does not cancel the others. Live access waits until Rafael chooses how OLX may be read.

## Tests

`uv run pytest` loads `config.test_settings`, an in-memory SQLite overlay. It covers the portal, signup, session, free-trial pages, plan activation, credit reload, creating a radar, and storing a recorded ZAP payload, a recorded Viva Real payload, and a recorded OLX payload. PostgreSQL is not required, and neither is Redis. Isolation tests are skipped, including the free-search counter, the plan, the credit balance, and the radar. The account-context helper does not call `set_config` on SQLite. The application engine in `config.settings` stays PostgreSQL. Pytest mocks the Celery `delay` call and runs the task function directly. The ZAP tests call `coletar_zap` in process with the fixture file. The Viva Real tests call `coletar_viva_real` in process with its fixture file. The OLX tests call `coletar_olx` in process with its fixture file. They do not open the broker and they do not call the site.

`uv run pytest --ds config.postgres_settings` runs the same suite, including isolation, against the local PostgreSQL server. It needs the `rondimob` database and the owner role from the install steps. The Django connection for that command is the table owner. The isolation tests also connect as `rondimob_web` and `rondimob_worker` and check that one account cannot read the other. The free-search counter check, the plan check, the credit check, and the radar check connect as `rondimob_web`.

```bash
uv sync
uv run pytest
uv run pytest --ds config.postgres_settings
```
