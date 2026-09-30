import sys
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from contas.cota import (
    aceitar_pesquisa,
    ativar_plano,
    pode_configurar_alerta,
    pode_favoritar,
    pode_pesquisar,
    pesquisas_restantes,
)
from contas.models import Conta

SENHA = "senha-segura"
FUSO = ZoneInfo("America/Sao_Paulo")
JANEIRO = datetime(2026, 1, 15, 12, 0, tzinfo=FUSO)
FEVEREIRO = datetime(2026, 2, 1, 0, 0, tzinfo=FUSO)
CONTATO = "O plano Personalizado é por contato."


def _criar(**kwargs):
    dados = {
        "email": "ana@exemplo.com",
        "password": SENHA,
        "tipo": Conta.TIPO_CORRETOR,
        "nome": "Ana Lima",
        "telefone": "11987654321",
        "creci": "123456-SP",
    }
    dados.update(kwargs)
    return Conta.objects.create_user(**dados)


def _entrar(cliente, conta):
    resposta = cliente.post("/entrar/", {"email": conta.email, "senha": SENHA})
    if resposta.status_code != 302:
        raise AssertionError(resposta.status_code)
    return resposta


def _definir_usadas(conta, usadas, mes):
    conta.pesquisas_mes_usadas = usadas
    conta.mes_da_cota = mes
    conta.save(update_fields=["pesquisas_mes_usadas", "mes_da_cota"])


class AtivarPlanoTests(TestCase):
    def test_open_trial_area_offers_paid_plans_and_contact(self):
        conta = _criar(email="aberta@exemplo.com")
        _entrar(self.client, conta)
        area = self.client.get("/area/")
        self.assertContains(area, "10 pesquisas restantes")
        self.assertContains(area, "Ativar Padrão")
        self.assertContains(area, "Ativar Plus")
        self.assertContains(area, CONTATO)
        self.assertNotContains(area, 'name="plano" value="personalizado"')

    def test_anonymous_post_redirects_to_login(self):
        resposta = self.client.post("/area/plano/", {"plano": "padrao"})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta["Location"], "/entrar/")

    def test_padrao_stores_thirty_searches_and_imports_no_gateway(self):
        conta = _criar()
        _entrar(self.client, conta)
        antes = set(sys.modules)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            resposta = self.client.post("/area/plano/", {"plano": "padrao"})
        novos = set(sys.modules) - antes
        self.assertFalse(
            any("mercadopago" in nome or "stripe" in nome for nome in novos)
        )
        self.assertNotIn("mercadopago", sys.modules)
        self.assertNotIn("stripe", sys.modules)
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta["Location"], "/area/")
        conta.refresh_from_db()
        self.assertEqual(conta.plano, Conta.PLANO_PADRAO)
        self.assertEqual(conta.pesquisas_mes_usadas, 0)
        self.assertEqual(conta.mes_da_cota, date(2026, 1, 1))
        self.assertEqual(conta.pesquisas_gratis_usadas, 0)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertEqual(pesquisas_restantes(conta), 30)
            area = self.client.get("/area/")
        conta.refresh_from_db()
        self.assertEqual(area.status_code, 200)
        self.assertContains(area, "Padrão")
        self.assertContains(area, "30 pesquisas restantes")
        self.assertContains(area, "Ativar Padrão")
        self.assertContains(area, "Ativar Plus")
        self.assertContains(area, CONTATO)
        self.assertNotContains(area, "Resultados")
        self.assertEqual(conta.pesquisas_mes_usadas, 0)
        self.assertEqual(conta.pesquisas_gratis_usadas, 0)

        texto = "\n".join(
            caminho.read_text(encoding="utf-8")
            for caminho in Path("contas").rglob("*.py")
            if "tests" not in caminho.parts
        )
        for nome in ("mercadopago", "stripe", "Mercado Pago", "Stripe"):
            self.assertNotIn(nome, texto)

    def test_plus_keeps_the_used_count_and_raises_the_cap(self):
        conta = _criar()
        _entrar(self.client, conta)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertEqual(
                self.client.post("/area/plano/", {"plano": "padrao"}).status_code,
                302,
            )
        conta.refresh_from_db()
        _definir_usadas(conta, 5, date(2026, 1, 1))
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            resposta = self.client.post("/area/plano/", {"plano": "plus"})
        self.assertEqual(resposta.status_code, 302)
        conta.refresh_from_db()
        self.assertEqual(conta.plano, Conta.PLANO_PLUS)
        self.assertEqual(conta.pesquisas_mes_usadas, 5)
        self.assertEqual(conta.mes_da_cota, date(2026, 1, 1))
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertEqual(pesquisas_restantes(conta), 95)
            area = self.client.get("/area/")
        self.assertContains(area, "Plus")
        self.assertContains(area, "95 pesquisas restantes")
        self.assertTrue(pode_favoritar(conta))
        self.assertTrue(pode_configurar_alerta(conta))
        self.assertTrue(pode_pesquisar(conta))

    def test_personalizado_asks_for_contact_and_writes_nothing(self):
        conta = _criar()
        conta.pesquisas_gratis_usadas = 2
        conta.save(update_fields=["pesquisas_gratis_usadas"])
        _entrar(self.client, conta)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            aberta = self.client.get("/area/")
            resposta = self.client.post("/area/plano/", {"plano": "personalizado"})
        self.assertEqual(aberta.status_code, 200)
        self.assertNotContains(aberta, "R$ 97 por mês")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta["Location"], "/area/")
        self.assertContains(self.client.get("/area/"), CONTATO)
        conta.refresh_from_db()
        self.assertEqual(conta.plano, "")
        self.assertEqual(conta.pesquisas_gratis_usadas, 2)
        self.assertEqual(conta.pesquisas_mes_usadas, 0)
        self.assertIsNone(conta.mes_da_cota)

        bloqueada = _criar(email="bloqueada@exemplo.com")
        bloqueada.pesquisas_gratis_usadas = 10
        bloqueada.save(update_fields=["pesquisas_gratis_usadas"])
        _entrar(self.client, bloqueada)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            area = self.client.get("/area/")
        self.assertContains(area, CONTATO)
        self.assertContains(area, "sob consulta")
        self.assertContains(area, "Ativar Padrão")
        self.assertContains(area, "Ativar Plus")
        self.assertNotContains(area, 'name="plano" value="personalizado"')
        bloqueada.refresh_from_db()
        self.assertEqual(bloqueada.plano, "")
        self.assertEqual(bloqueada.pesquisas_gratis_usadas, 10)

    def test_month_turn_restarts_plus_at_one_hundred(self):
        conta = _criar()
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertTrue(ativar_plano(conta, Conta.PLANO_PLUS))
        _definir_usadas(conta, 10, date(2026, 1, 1))
        _entrar(self.client, conta)
        with patch("django.utils.timezone.now", return_value=FEVEREIRO):
            self.assertEqual(pesquisas_restantes(conta), 100)
            area = self.client.get("/area/")
            self.assertTrue(aceitar_pesquisa(conta))
        self.assertContains(area, "100 pesquisas restantes")
        conta.refresh_from_db()
        self.assertEqual(conta.plano, Conta.PLANO_PLUS)
        self.assertEqual(conta.pesquisas_mes_usadas, 1)
        self.assertEqual(conta.mes_da_cota, date(2026, 2, 1))
        self.assertEqual(conta.pesquisas_gratis_usadas, 0)
        with patch("django.utils.timezone.now", return_value=FEVEREIRO):
            self.assertEqual(pesquisas_restantes(conta), 99)

    def test_empty_paid_quota_shows_saved_results_and_refuses_a_search(self):
        conta = _criar()
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertTrue(ativar_plano(conta, Conta.PLANO_PADRAO))
        _definir_usadas(conta, 30, date(2026, 1, 1))
        _entrar(self.client, conta)
        with (
            patch("django.utils.timezone.now", return_value=JANEIRO),
            CaptureQueriesContext(connection) as consultas,
        ):
            self.assertFalse(aceitar_pesquisa(conta))
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertFalse(pode_pesquisar(conta))
            self.assertTrue(pode_favoritar(conta))
            self.assertTrue(pode_configurar_alerta(conta))
            area = self.client.get("/area/")
        updates = [
            item["sql"]
            for item in consultas.captured_queries
            if item["sql"].lstrip().upper().startswith("UPDATE")
        ]
        self.assertEqual(updates, [])
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_mes_usadas, 30)
        self.assertEqual(conta.plano, Conta.PLANO_PADRAO)
        self.assertEqual(area.status_code, 200)
        self.assertContains(area, "Resultados")
        self.assertContains(area, "Padrão")
        self.assertContains(area, "0 pesquisas restantes")
        self.assertNotContains(area, "<li>")

    def test_free_trial_still_spends_only_the_free_counter(self):
        conta = _criar()
        _entrar(self.client, conta)
        with patch("django.utils.timezone.now", return_value=conta.criada_em):
            area = self.client.get("/area/")
            self.assertTrue(aceitar_pesquisa(conta))
        self.assertContains(area, "10 pesquisas restantes")
        self.assertNotContains(area, "R$ 97 por mês")
        conta.refresh_from_db()
        self.assertEqual(conta.plano, "")
        self.assertEqual(conta.pesquisas_gratis_usadas, 1)
        self.assertEqual(conta.pesquisas_mes_usadas, 0)
        self.assertIsNone(conta.mes_da_cota)

    def test_paid_plan_still_spends_the_month_after_the_free_trial_is_closed(self):
        conta = _criar(email="paga-fechada@exemplo.com")
        conta.pesquisas_gratis_usadas = 10
        conta.save(update_fields=["pesquisas_gratis_usadas"])
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertTrue(ativar_plano(conta, Conta.PLANO_PADRAO))
            self.assertEqual(pesquisas_restantes(conta), 30)
            self.assertTrue(aceitar_pesquisa(conta))
            self.assertTrue(pode_favoritar(conta))
            self.assertTrue(pode_configurar_alerta(conta))
            self.assertTrue(pode_pesquisar(conta))
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_mes_usadas, 1)
        self.assertEqual(conta.pesquisas_gratis_usadas, 10)

    def test_exhausted_month_restarts_on_the_next_accept(self):
        conta = _criar(email="vira-mes@exemplo.com")
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertTrue(ativar_plano(conta, Conta.PLANO_PADRAO))
        _definir_usadas(conta, 30, date(2026, 1, 1))
        with patch("django.utils.timezone.now", return_value=FEVEREIRO):
            self.assertEqual(pesquisas_restantes(conta), 30)
            self.assertTrue(aceitar_pesquisa(conta))
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_mes_usadas, 1)
        self.assertEqual(conta.mes_da_cota, date(2026, 2, 1))

    def test_one_monthly_search_left_uses_the_singular(self):
        conta = _criar(email="uma-mes@exemplo.com")
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertTrue(ativar_plano(conta, Conta.PLANO_PADRAO))
        _definir_usadas(conta, 29, date(2026, 1, 1))
        _entrar(self.client, conta)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            area = self.client.get("/area/")
        self.assertContains(area, "1 pesquisa restante")
        self.assertNotContains(area, "1 pesquisas restantes")

    def test_switch_to_padrao_after_more_than_thirty_clamps_at_zero(self):
        conta = _criar(email="troca@exemplo.com")
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertTrue(ativar_plano(conta, Conta.PLANO_PLUS))
        _definir_usadas(conta, 40, date(2026, 1, 1))
        _entrar(self.client, conta)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            resposta = self.client.post("/area/plano/", {"plano": "padrao"})
            area = self.client.get("/area/")
        self.assertEqual(resposta.status_code, 302)
        conta.refresh_from_db()
        self.assertEqual(conta.plano, Conta.PLANO_PADRAO)
        self.assertEqual(conta.pesquisas_mes_usadas, 40)
        self.assertContains(area, "0 pesquisas restantes")
        self.assertContains(area, "Resultados")
        self.assertNotContains(area, "-10")


class MigracaoPlanoTests(TestCase):
    def test_column_migration_does_not_add_a_policy(self):
        texto = Path("contas/migrations/0004_plano_pago.py").read_text(encoding="utf-8")
        self.assertNotIn("POLICY", texto.upper())
        self.assertNotIn("ROW LEVEL SECURITY", texto.upper())
        self.assertNotIn("ENABLE", texto.upper())
        self.assertNotIn("FORCE", texto.upper())
        self.assertIn("plano", texto)
        self.assertIn("pesquisas_mes_usadas", texto)
        self.assertIn("mes_da_cota", texto)
