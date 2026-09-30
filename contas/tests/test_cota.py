from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from contas.cota import (
    aceitar_pesquisa,
    data_de_criacao,
    nomes_de_radar,
    pode_configurar_alerta,
    pode_favoritar,
    pode_pesquisar,
    ultimo_dia_aberto,
)
from contas.isolamento import definir_conta
from contas.models import Conta

SENHA = "senha-segura"
FUSO = ZoneInfo("America/Sao_Paulo")
CORRETOR = {
    "tipo": "corretor",
    "nome": "Ana Lima",
    "email": "ana@exemplo.com",
    "telefone": "11987654321",
    "senha": SENHA,
    "creci": "123456-SP",
}
PRECOS = (
    "Grátis",
    "R$ 0",
    "10 pesquisas em 14 dias",
    "Padrão",
    "R$ 97 por mês",
    "30 pesquisas",
    "Plus",
    "R$ 197 por mês",
    "100 pesquisas",
    "Personalizado",
    "sob consulta",
)


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


def _definir_usadas(conta, usadas):
    conta.pesquisas_gratis_usadas = usadas
    conta.save(update_fields=["pesquisas_gratis_usadas"])


def _definir_criacao(conta, momento):
    conta.criada_em = momento
    conta.save(update_fields=["criada_em"])


class CotaGratisTests(TestCase):
    def test_new_account_shows_ten_searches_and_the_last_open_day(self):
        anonima = self.client.get("/area/")
        self.assertEqual(anonima.status_code, 302)
        self.assertEqual(anonima["Location"], "/entrar/")

        conta = _criar()
        criacao = conta.criada_em.astimezone(FUSO).date()
        ultimo = criacao + timedelta(days=13)
        self.assertEqual(conta.pesquisas_gratis_usadas, 0)
        self.assertEqual(data_de_criacao(conta), criacao)
        self.assertEqual(ultimo_dia_aberto(conta), ultimo)
        self.assertEqual(nomes_de_radar(conta), [])

        _entrar(self.client, conta)
        with patch("django.utils.timezone.now", return_value=conta.criada_em):
            self.assertTrue(pode_pesquisar(conta))
            self.assertTrue(pode_favoritar(conta))
            self.assertTrue(pode_configurar_alerta(conta))
            area = self.client.get("/area/")
        conta.refresh_from_db()
        self.assertEqual(area.status_code, 200)
        self.assertContains(area, "10 pesquisas restantes")
        self.assertContains(area, f"Último dia aberto: {ultimo.strftime('%d/%m/%Y')}")
        self.assertNotContains(area, "R$ 97 por mês")
        self.assertNotContains(area, "Radares")
        self.assertEqual(conta.pesquisas_gratis_usadas, 0)

    def test_accepted_search_is_the_only_change_to_the_counter(self):
        conta = _criar()
        _definir_usadas(conta, 3)
        _entrar(self.client, conta)

        antes = self.client.get("/area/")
        self.assertContains(antes, "7 pesquisas restantes")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 3)

        with (
            patch("contas.cota.definir_conta", wraps=definir_conta) as definir,
            patch(
                "contas.models.Conta.objects.select_for_update",
                wraps=Conta.objects.select_for_update,
            ) as travar,
        ):
            self.assertTrue(aceitar_pesquisa(conta))
        definir.assert_called_with(conta.pk)
        travar.assert_called()
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 4)

        self.client.get("/")
        self.client.get("/area/")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 4)
        depois = self.client.get("/area/")
        self.assertContains(depois, "6 pesquisas restantes")

        self.assertTrue(aceitar_pesquisa(conta))
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 5)
        segunda = self.client.get("/area/")
        self.assertContains(segunda, "5 pesquisas restantes")

    def test_signup_login_home_and_area_do_not_spend_a_search(self):
        criada = self.client.post("/criar-conta/", CORRETOR)
        self.assertEqual(criada.status_code, 302)
        conta = Conta.objects.get(email="ana@exemplo.com")
        self.assertEqual(conta.pesquisas_gratis_usadas, 0)

        area = self.client.get("/area/")
        self.assertEqual(area.status_code, 200)
        self.client.get("/")
        self.client.post("/sair/")
        self.client.post("/entrar/", {"email": conta.email, "senha": SENHA})
        self.client.get("/area/")
        self.client.get("/")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 0)

    def test_tenth_search_closes_the_gates_and_the_eleventh_does_not_write(self):
        conta = _criar()
        _definir_usadas(conta, 9)
        self.assertTrue(pode_pesquisar(conta))
        self.assertTrue(pode_favoritar(conta))
        self.assertTrue(pode_configurar_alerta(conta))
        _entrar(self.client, conta)
        aberta = self.client.get("/area/")
        self.assertContains(aberta, "1 pesquisa restante")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 9)

        self.assertTrue(aceitar_pesquisa(conta))
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 10)
        self.assertFalse(pode_pesquisar(conta))
        self.assertFalse(pode_favoritar(conta))
        self.assertFalse(pode_configurar_alerta(conta))

        bloqueada = self.client.get("/area/")
        self.assertEqual(bloqueada.status_code, 200)
        for texto in PRECOS:
            self.assertContains(bloqueada, texto)
        self.assertContains(bloqueada, "Radares")
        self.assertNotContains(bloqueada, "<li>")
        self.assertNotContains(bloqueada, "pesquisa restante")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 10)

        with CaptureQueriesContext(connection) as consultas:
            self.assertFalse(aceitar_pesquisa(conta))
        updates = [
            item["sql"]
            for item in consultas.captured_queries
            if item["sql"].lstrip().upper().startswith("UPDATE")
        ]
        self.assertEqual(updates, [])
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 10)
        self.assertFalse(pode_pesquisar(conta))
        self.assertFalse(pode_favoritar(conta))
        self.assertFalse(pode_configurar_alerta(conta))

    def test_day_14_accepts_and_day_15_shows_plans_without_spending(self):
        dia_1 = datetime(2026, 9, 1, 12, 0, tzinfo=FUSO)
        dia_14 = datetime(2026, 9, 14, 23, 59, tzinfo=FUSO)
        dia_15 = datetime(2026, 9, 15, 0, 0, tzinfo=FUSO)

        aberta = _criar(email="aberta@exemplo.com")
        _definir_criacao(aberta, dia_1)
        self.assertEqual(data_de_criacao(aberta), date(2026, 9, 1))
        self.assertEqual(ultimo_dia_aberto(aberta), date(2026, 9, 14))
        with patch("django.utils.timezone.now", return_value=dia_14):
            self.assertTrue(pode_pesquisar(aberta))
            self.assertTrue(aceitar_pesquisa(aberta))
        aberta.refresh_from_db()
        self.assertEqual(aberta.pesquisas_gratis_usadas, 1)

        bloqueada = _criar(email="bloqueada@exemplo.com")
        _definir_criacao(bloqueada, dia_1)
        _entrar(self.client, bloqueada)
        with patch("django.utils.timezone.now", return_value=dia_15):
            self.assertFalse(pode_pesquisar(bloqueada))
            self.assertFalse(pode_favoritar(bloqueada))
            self.assertFalse(pode_configurar_alerta(bloqueada))
            with CaptureQueriesContext(connection) as consultas:
                self.assertFalse(aceitar_pesquisa(bloqueada))
            area = self.client.get("/area/")
        updates = [
            item["sql"]
            for item in consultas.captured_queries
            if item["sql"].lstrip().upper().startswith("UPDATE")
        ]
        self.assertEqual(updates, [])
        bloqueada.refresh_from_db()
        self.assertEqual(bloqueada.pesquisas_gratis_usadas, 0)
        self.assertEqual(area.status_code, 200)
        for texto in PRECOS:
            self.assertContains(area, texto)
        self.assertContains(area, "Radares")
        self.assertNotContains(area, "<li>")
        self.assertNotContains(area, "Último dia aberto")
        self.assertNotContains(area, "pesquisa restante")

        with (
            patch("django.utils.timezone.now", return_value=dia_15),
            patch("contas.views.nomes_de_radar", return_value=["Radar Centro"]),
        ):
            com_nome = self.client.get("/area/")
        self.assertContains(com_nome, "Radar Centro")
        bloqueada.refresh_from_db()
        self.assertEqual(bloqueada.pesquisas_gratis_usadas, 0)

    def test_utc_instant_just_after_midnight_belongs_to_the_previous_local_date(self):
        criada_em = datetime(2026, 9, 1, 2, 30, tzinfo=ZoneInfo("UTC"))
        ultimo_aberto = datetime(2026, 9, 13, 23, 59, tzinfo=FUSO)
        primeiro_bloqueado = datetime(2026, 9, 14, 0, 30, tzinfo=FUSO)

        conta = _criar()
        _definir_criacao(conta, criada_em)
        self.assertEqual(data_de_criacao(conta), date(2026, 8, 31))
        self.assertEqual(ultimo_dia_aberto(conta), date(2026, 9, 13))

        _entrar(self.client, conta)
        dentro = datetime(2026, 9, 1, 12, 0, tzinfo=FUSO)
        with patch("django.utils.timezone.now", return_value=dentro):
            area = self.client.get("/area/")
        self.assertContains(area, "10 pesquisas restantes")
        self.assertContains(area, "Último dia aberto: 13/09/2026")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 0)

        with patch("django.utils.timezone.now", return_value=ultimo_aberto):
            self.assertTrue(aceitar_pesquisa(conta))
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 1)

        outra = _criar(email="borda@exemplo.com")
        _definir_criacao(outra, criada_em)
        with patch("django.utils.timezone.now", return_value=primeiro_bloqueado):
            self.assertFalse(aceitar_pesquisa(outra))
            self.assertFalse(pode_pesquisar(outra))
            self.assertFalse(pode_favoritar(outra))
            self.assertFalse(pode_configurar_alerta(outra))
        outra.refresh_from_db()
        self.assertEqual(outra.pesquisas_gratis_usadas, 0)


class MigracaoCotaTests(TestCase):
    def test_column_migration_does_not_add_a_policy(self):
        texto = Path("contas/migrations/0003_cota_gratis.py").read_text(encoding="utf-8")
        self.assertNotIn("POLICY", texto.upper())
        self.assertNotIn("ROW LEVEL SECURITY", texto.upper())
        self.assertNotIn("ENABLE", texto.upper())
        self.assertIn("criada_em", texto)
        self.assertIn("pesquisas_gratis_usadas", texto)
