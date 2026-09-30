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
uv run celery -A config worker --loglevel=info
```

## Tests

`uv run pytest` loads `config.test_settings`, an in-memory SQLite overlay. It covers the portal, signup, and session pages. PostgreSQL is not required, and neither is Redis. Isolation tests are skipped. The account-context helper does not call `set_config` on SQLite. The application engine in `config.settings` stays PostgreSQL. Pytest mocks the Celery `delay` call and runs the task function directly.

`uv run pytest --ds config.postgres_settings` runs the same suite, including isolation, against the local PostgreSQL server. It needs the `rondimob` database and the owner role from the install steps. The Django connection for that command is the table owner. The isolation tests also connect as `rondimob_web` and `rondimob_worker` and check that one account cannot read the other.

```bash
uv sync
uv run pytest
uv run pytest --ds config.postgres_settings
```
