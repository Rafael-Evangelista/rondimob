"""PostgreSQL suite for account isolation.

The default pytest module stays ``config.test_settings`` (SQLite).
Run ``uv run pytest --ds config.postgres_settings`` against a local server.
The Django connection is the table owner so migrate can create roles.
Isolation tests open their own connections as ``rondimob_web`` and ``rondimob_worker``.
"""

from config.settings import *  # noqa: F403
from config.settings import OWNER_DATABASE_URL, database_from_url

DATABASES = {"default": database_from_url(OWNER_DATABASE_URL)}
