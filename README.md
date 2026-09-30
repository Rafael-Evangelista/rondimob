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

Then, from this repository:

```bash
uv sync
export DATABASE_URL=postgresql:///rondimob
uv run python manage.py migrate
uv run python manage.py runserver
```

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

In another terminal, from this repository:

```bash
uv run celery -A config worker --loglevel=info
```

## Tests

Pytest loads `config.test_settings`, an in-memory SQLite overlay. A local PostgreSQL server is not required, and neither is Redis. The application engine in `config.settings` stays PostgreSQL. Pytest mocks the Celery `delay` call and runs the task function directly.

```bash
uv sync
uv run pytest
```
