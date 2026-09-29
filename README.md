# rondimob

Public portal and client area. The application database is PostgreSQL.

## Local PostgreSQL

Create the database and point `DATABASE_URL` at it. When that variable is unset, the app uses `postgresql://localhost/rondimob`.

```bash
createdb rondimob
export DATABASE_URL=postgresql://localhost/rondimob
uv run python manage.py migrate
uv run python manage.py runserver
```

Signup is at `http://localhost:8000/criar-conta/`.

## Tests

Pytest loads `config.test_settings`, an in-memory SQLite overlay. A local PostgreSQL server is not required. The application engine stays PostgreSQL in `config.settings`.

```bash
uv run pytest
```
