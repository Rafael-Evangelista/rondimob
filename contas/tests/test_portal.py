import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import celery
import django
from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.test import TestCase
from django.urls import reverse

from config import settings as production_settings
from config.settings import database_from_url, database_url_for_argv

PORTAL_COPY = (
    "O rondimob monitora preços por região e imobiliárias concorrentes no ABCD, "
    "em um só lugar."
)
CLIENT_AREA_LINK = '<a href="/entrar/">Área do cliente</a>'
STYLESHEET = "/static/contas/portal.css"


class PortalTests(TestCase):
    def test_anonymous_portal_shows_products_plans_pack_and_prices(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Produtos")
        self.assertContains(response, PORTAL_COPY)
        self.assertContains(response, "Monitoramento de preços por região no ABCD")
        self.assertContains(
            response,
            "Monitoramento de imobiliárias concorrentes no ABCD",
        )
        self.assertContains(response, "Planos")
        self.assertContains(response, "Grátis")
        self.assertContains(response, "R$ 0")
        self.assertContains(response, "10 pesquisas em 14 dias")
        self.assertContains(response, "Padrão")
        self.assertContains(response, "R$ 97 por mês")
        self.assertContains(response, "30 pesquisas")
        self.assertContains(response, "Plus")
        self.assertContains(response, "R$ 197 por mês")
        self.assertContains(response, "100 pesquisas")
        self.assertContains(response, "Personalizado")
        self.assertContains(response, "sob consulta")
        self.assertContains(response, "Pacote de créditos")
        self.assertContains(response, "R$ 47 por 10 pesquisas")
        self.assertNotIn("sessionid", response.cookies)

    def test_unknown_path_returns_framework_404(self):
        response = self.client.get("/caminho-que-nao-existe/")

        self.assertEqual(response.status_code, 404)

    def test_client_area_link_is_present_without_a_session(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, CLIENT_AREA_LINK, html=True)
        self.assertEqual(reverse("entrar"), "/entrar/")
        self.assertNotIn("sessionid", response.cookies)

    def test_entrar_confirms_client_area_without_authenticating(self):
        response = self.client.get("/entrar/")
        body = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("<form", body.lower())
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="senha"')
        self.assertContains(response, 'action="/entrar/"')
        self.assertNotIn("sessionid", response.cookies)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_public_pages_use_a_light_base(self):
        css_path = find("contas/portal.css")
        css = Path(css_path).read_text(encoding="utf-8").lower()

        self.assertIn("color-scheme: light only", css)
        self.assertIn("background: white", css)
        self.assertIn("color: black", css)
        self.assertNotIn("#", css)
        self.assertNotIn("prefers-color-scheme: dark", css)
        self.assertNotRegex(css, r"color-scheme:\s*dark")

        for path in ("/", "/entrar/", "/criar-conta/", "/recuperar-senha/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, STYLESHEET)
            self.assertNotContains(response, 'class="dark"')
            self.assertNotContains(response, 'data-theme="dark"')

    def test_django_version_and_postgresql_engine(self):
        self.assertEqual(django.get_version(), "6.1.1")
        self.assertEqual(
            production_settings.DATABASES["default"]["ENGINE"],
            "django.db.backends.postgresql",
        )
        active = settings.DATABASES["default"]
        if active["ENGINE"] == "django.db.backends.sqlite3":
            self.assertIn("memory", active["NAME"])
        else:
            self.assertEqual(active["ENGINE"], "django.db.backends.postgresql")
            self.assertNotIn(active["USER"], {"rondimob_web", "rondimob_worker"})
        self.assertEqual(
            database_from_url(
                "postgres://corret%6Fr:p%40ss@db.example:5432/rondimob/"
            ),
            {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "rondimob",
                "USER": "corretor",
                "PASSWORD": "p@ss",
                "HOST": "db.example",
                "PORT": "5432",
            },
        )
        with self.assertRaises(ValueError):
            database_from_url("mysql://localhost/rondimob")
        used_url = database_url_for_argv()
        expected = database_from_url(used_url)
        configured = production_settings.DATABASES["default"]
        self.assertEqual({key: configured[key] for key in expected}, expected)
        self.assertEqual(celery.__version__, "5.6.3")
        self.assertEqual(
            production_settings.CELERY_BROKER_URL,
            "redis://localhost:6379/0",
        )

    def test_database_url_follows_the_command(self):
        from config.settings import (
            OWNER_DATABASE_URL,
            WEB_DATABASE_URL,
            WORKER_DATABASE_URL,
            database_url_for_argv,
        )

        env = os.environ.copy()
        env.pop("DATABASE_URL", None)
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                database_url_for_argv(["manage.py", "migrate"]),
                OWNER_DATABASE_URL,
            )
            self.assertEqual(
                database_url_for_argv(["manage.py", "makemigrations", "contas"]),
                OWNER_DATABASE_URL,
            )
            self.assertEqual(
                database_url_for_argv(["/tmp/celery", "-A", "config", "worker"]),
                WORKER_DATABASE_URL,
            )
            self.assertEqual(
                database_url_for_argv(["python", "-m", "celery", "worker"]),
                WORKER_DATABASE_URL,
            )
            self.assertEqual(
                database_url_for_argv(["manage.py", "runserver"]),
                WEB_DATABASE_URL,
            )
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://explicit/rondimob"}):
            self.assertEqual(
                database_url_for_argv(["manage.py", "migrate"]),
                "postgresql://explicit/rondimob",
            )

    def test_celery_autodiscovers_the_recovery_task(self):
        import redis

        self.assertIsNotNone(redis)
        codigo = "\n".join(
            [
                "from config.celery import app",
                "app.loader.import_default_modules()",
                "assert app.conf.broker_url == 'redis://localhost:6379/0'",
                "registrada = 'contas.tasks.preparar_link_de_recuperacao'",
                "assert registrada in app.tasks",
            ]
        )
        concluido = subprocess.run(
            [sys.executable, "-c", codigo],
            cwd=Path(__file__).resolve().parents[2],
            env={**os.environ, "DJANGO_SETTINGS_MODULE": "config.test_settings"},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            concluido.returncode,
            0,
            concluido.stderr + concluido.stdout,
        )
