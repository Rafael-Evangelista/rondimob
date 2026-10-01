"""Django settings for the rondimob public portal."""

import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-not-for-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").strip().lower() in {"1", "true", "yes"}

_allowed_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "").strip()
if not _allowed_hosts:
    _allowed_hosts = "localhost,127.0.0.1,testserver"
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "contas",
    "radares",
    "anuncios",
    "coleta",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "contas.middleware.IsolamentoDaContaMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "contas.Conta"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

OWNER_DATABASE_URL = "postgresql:///rondimob"
WEB_DATABASE_URL = "postgresql://rondimob_web:dev-only-web@127.0.0.1/rondimob"
WORKER_DATABASE_URL = "postgresql://rondimob_worker:dev-only-worker@127.0.0.1/rondimob"
DEFAULT_DATABASE_URL = OWNER_DATABASE_URL


def database_url_for_argv(argv=None):
    """Owner for migrate, worker for Celery, web otherwise.

    An explicit DATABASE_URL replaces that choice for every command.
    """
    explicit = os.environ.get("DATABASE_URL", "").strip()
    if explicit:
        return explicit
    argv = list(sys.argv if argv is None else argv)
    if _argv_e_celery(argv):
        return WORKER_DATABASE_URL
    command = argv[1] if len(argv) > 1 else ""
    if command in {"migrate", "makemigrations"}:
        return OWNER_DATABASE_URL
    return WEB_DATABASE_URL


def _argv_e_celery(argv):
    nomes = {Path(parte).name.lower() for parte in argv[:4]}
    return "celery" in nomes or any(nome.startswith("celery") for nome in nomes)


def database_from_url(url):
    """Map a PostgreSQL URL to Django's DATABASES entry."""
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("DATABASE_URL must use the postgres or postgresql scheme")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path).strip("/"),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": "" if parsed.port is None else str(parsed.port),
    }


DATABASES = {
    "default": database_from_url(database_url_for_argv()),
}

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_TASK_ROUTES = {
    "coleta.tasks.coletar_zap": {"queue": "zap"},
    "coleta.tasks.coletar_viva_real": {"queue": "viva-real"},
}
