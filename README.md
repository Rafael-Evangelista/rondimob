# rondimob

Public portal and client area. The application database is PostgreSQL. Python 3.13.15 and Django 6.1.1.

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

## Tests

Pytest loads `config.test_settings`, an in-memory SQLite overlay. A local PostgreSQL server is not required. The application engine in `config.settings` stays PostgreSQL.

```bash
uv sync
uv run pytest
```
