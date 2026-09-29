import os
from pathlib import Path

import django
from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.test import SimpleTestCase
from django.urls import reverse

from config import settings as production_settings
from config.settings import DEFAULT_DATABASE_URL, database_from_url

PORTAL_COPY = (
    "O rondimob monitora preços por região e imobiliárias concorrentes no ABCD, "
    "em um só lugar."
)
CLIENT_AREA_LINK = '<a href="/entrar/">Área do cliente</a>'
STYLESHEET = "/static/contas/portal.css"


class PortalTests(SimpleTestCase):
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
        self.assertContains(response, "A área do cliente fica neste site.")
        self.assertContains(response, "O acesso vai pedir e-mail e senha.")
        self.assertNotIn("<form", body.lower())
        self.assertNotIn("<input", body.lower())
        self.assertNotIn("<button", body.lower())
        self.assertNotIn("sessionid", response.cookies)

    def test_public_pages_use_a_light_base(self):
        css_path = find("contas/portal.css")
        css = Path(css_path).read_text(encoding="utf-8").lower()

        self.assertIn("color-scheme: light only", css)
        self.assertIn("background: white", css)
        self.assertIn("color: black", css)
        self.assertNotIn("#", css)
        self.assertNotIn("prefers-color-scheme: dark", css)
        self.assertNotRegex(css, r"color-scheme:\s*dark")

        for path in ("/", "/entrar/", "/criar-conta/"):
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
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"],
            "django.db.backends.sqlite3",
        )
        self.assertIn("memory", settings.DATABASES["default"]["NAME"])
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
        used_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
        expected = database_from_url(used_url)
        configured = production_settings.DATABASES["default"]
        self.assertEqual({key: configured[key] for key in expected}, expected)
