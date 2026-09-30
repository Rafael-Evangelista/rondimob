import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import TestCase

from contas.cota import (
    aceitar_pesquisa,
    ativar_plano,
    pode_configurar_alerta,
    pode_favoritar,
    pode_pesquisar,
    saldo_credito,
)
from contas.models import Conta, Credito

SENHA = "senha-segura"
FUSO = ZoneInfo("America/Sao_Paulo")
JANEIRO = datetime(2026, 1, 15, 12, 0, tzinfo=FUSO)
JANEIRO_TARDE = datetime(2026, 1, 15, 18, 0, tzinfo=FUSO)
FEVEREIRO = datetime(2026, 2, 1, 0, 0, tzinfo=FUSO)
PRECO = Decimal("47.00")
AVISO = "Ative um plano para recarregar."


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


def _ativar(conta, plano, quando=JANEIRO):
    with patch("django.utils.timezone.now", return_value=quando):
        if not ativar_plano(conta, plano):
            raise AssertionError(plano)
    conta.refresh_from_db()
    return conta


def _recarregar(cliente, quando=JANEIRO):
    with patch("django.utils.timezone.now", return_value=quando):
        return cliente.post("/area/credito/")


class RecarregarCreditoTests(TestCase):
    def test_reload_stores_ten_searches_at_47_without_a_gateway(self):
        anonima = self.client.post("/area/credito/")
        self.assertEqual(anonima.status_code, 302)
        self.assertEqual(anonima["Location"], "/entrar/")
        self.assertEqual(Credito.objects.count(), 0)

        for plano, email in (
            (Conta.PLANO_PADRAO, "padrao@exemplo.com"),
            (Conta.PLANO_PLUS, "plus@exemplo.com"),
        ):
            with self.subTest(plano=plano):
                conta = _criar(email=email)
                _ativar(conta, plano)
                _entrar(self.client, conta)
                antes = set(sys.modules)
                resposta = _recarregar(self.client)
                novos = set(sys.modules) - antes
                self.assertFalse(
                    any("mercadopago" in nome or "stripe" in nome for nome in novos)
                )
                self.assertEqual(resposta.status_code, 302)
                self.assertEqual(resposta["Location"], "/area/")
                pacote = Credito.objects.get(conta=conta)
                self.assertEqual(pacote.restante, 10)
                self.assertEqual(pacote.preco, PRECO)
                self.assertEqual(saldo_credito(conta), 10)
                conta.refresh_from_db()
                self.assertEqual(conta.plano, plano)
                self.assertEqual(conta.pesquisas_mes_usadas, 0)
                self.assertEqual(conta.mes_da_cota, date(2026, 1, 1))
                with patch("django.utils.timezone.now", return_value=JANEIRO):
                    antes_linhas = Credito.objects.filter(conta=conta).count()
                    area = self.client.get("/area/")
                self.assertEqual(Credito.objects.filter(conta=conta).count(), antes_linhas)
                conta.refresh_from_db()
                self.assertEqual(conta.pesquisas_mes_usadas, 0)
                self.assertEqual(area.status_code, 200)
                self.assertContains(area, "10 créditos")
                self.assertContains(area, "R$ 47 por 10 pesquisas")
                self.assertContains(area, ">Recarregar<")
                self.client.post("/sair/")

        texto = "\n".join(
            caminho.read_text(encoding="utf-8")
            for caminho in Path("contas").rglob("*.py")
            if "tests" not in caminho.parts
        )
        for nome in ("mercadopago", "stripe", "Mercado Pago", "Stripe"):
            self.assertNotIn(nome, texto)
        self.assertFalse(any(nome in Conta._meta.fields_map for nome in ("saldo", "credito")))
        self.assertNotIn("saldo", {campo.name for campo in Conta._meta.fields})

    def test_second_reload_adds_ten_more(self):
        conta = _criar(email="duas@exemplo.com")
        _ativar(conta, Conta.PLANO_PADRAO)
        _definir_usadas(conta, 4, date(2026, 1, 1))
        _entrar(self.client, conta)
        self.assertEqual(_recarregar(self.client).status_code, 302)
        self.assertEqual(_recarregar(self.client, JANEIRO_TARDE).status_code, 302)
        self.assertEqual(Credito.objects.filter(conta=conta).count(), 2)
        self.assertEqual(saldo_credito(conta), 20)
        self.assertEqual(
            list(Credito.objects.filter(conta=conta).values_list("preco", flat=True)),
            [PRECO, PRECO],
        )
        conta.refresh_from_db()
        self.assertEqual(conta.plano, Conta.PLANO_PADRAO)
        self.assertEqual(conta.pesquisas_mes_usadas, 4)
        self.assertEqual(conta.mes_da_cota, date(2026, 1, 1))

    def test_open_month_spends_the_month_and_keeps_the_balance(self):
        conta = _criar(email="mes@exemplo.com")
        _ativar(conta, Conta.PLANO_PADRAO)
        _entrar(self.client, conta)
        _recarregar(self.client)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertTrue(aceitar_pesquisa(conta))
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_mes_usadas, 1)
        self.assertEqual(conta.mes_da_cota, date(2026, 1, 1))
        self.assertEqual(saldo_credito(conta), 10)
        self.assertEqual(Credito.objects.get(conta=conta).restante, 10)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            area = self.client.get("/area/")
        self.assertContains(area, "10 créditos")
        self.assertContains(area, "29 pesquisas restantes")
        self.assertNotContains(area, "Resultados")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_mes_usadas, 1)
        self.assertEqual(saldo_credito(conta), 10)

    def test_exhausted_month_spends_credit_and_leaves_the_counter(self):
        conta = _criar(email="cheio@exemplo.com")
        _ativar(conta, Conta.PLANO_PLUS)
        _definir_usadas(conta, 100, date(2026, 1, 1))
        _entrar(self.client, conta)
        _recarregar(self.client)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertTrue(pode_pesquisar(conta))
            self.assertTrue(pode_favoritar(conta))
            self.assertTrue(pode_configurar_alerta(conta))
            self.assertTrue(aceitar_pesquisa(conta))
            area = self.client.get("/area/")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_mes_usadas, 100)
        self.assertEqual(conta.plano, Conta.PLANO_PLUS)
        self.assertEqual(saldo_credito(conta), 9)
        self.assertEqual(Credito.objects.get(conta=conta).restante, 9)
        self.assertContains(area, "9 créditos")
        self.assertContains(area, "0 pesquisas restantes")
        self.assertNotContains(area, "Resultados")
        self.assertContains(area, ">Recarregar<")

    def test_spend_uses_the_oldest_package_that_still_has_units(self):
        conta = _criar(email="antigo@exemplo.com")
        _ativar(conta, Conta.PLANO_PADRAO)
        _definir_usadas(conta, 30, date(2026, 1, 1))
        _entrar(self.client, conta)
        _recarregar(self.client, JANEIRO)
        _recarregar(self.client, JANEIRO_TARDE)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertTrue(aceitar_pesquisa(conta))
            self.assertTrue(aceitar_pesquisa(conta))
        pacotes = list(Credito.objects.filter(conta=conta).order_by("criado_em", "id"))
        self.assertEqual([pacote.restante for pacote in pacotes], [8, 10])
        self.assertEqual(saldo_credito(conta), 18)
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_mes_usadas, 30)
        pacotes[0].restante = 1
        pacotes[0].save(update_fields=["restante"])
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertTrue(aceitar_pesquisa(conta))
            self.assertTrue(aceitar_pesquisa(conta))
        pacotes = list(Credito.objects.filter(conta=conta).order_by("criado_em", "id"))
        self.assertEqual([pacote.restante for pacote in pacotes], [0, 9])
        self.assertEqual(saldo_credito(conta), 9)
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_mes_usadas, 30)

    def test_month_turn_keeps_the_balance_and_spends_the_new_month(self):
        conta = _criar(email="vira@exemplo.com")
        _ativar(conta, Conta.PLANO_PADRAO)
        _definir_usadas(conta, 30, date(2026, 1, 1))
        _entrar(self.client, conta)
        _recarregar(self.client)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertTrue(aceitar_pesquisa(conta))
        self.assertEqual(saldo_credito(conta), 9)
        with patch("django.utils.timezone.now", return_value=FEVEREIRO):
            self.assertEqual(saldo_credito(conta), 9)
            area = self.client.get("/area/")
            self.assertTrue(aceitar_pesquisa(conta))
        self.assertContains(area, "9 créditos")
        self.assertContains(area, "30 pesquisas restantes")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_mes_usadas, 1)
        self.assertEqual(conta.mes_da_cota, date(2026, 2, 1))
        self.assertEqual(conta.plano, Conta.PLANO_PADRAO)
        self.assertEqual(saldo_credito(conta), 9)
        self.assertEqual(Credito.objects.get(conta=conta).restante, 9)

    def test_plan_switch_does_not_reset_credit(self):
        conta = _criar(email="troca@exemplo.com")
        _ativar(conta, Conta.PLANO_PLUS)
        _entrar(self.client, conta)
        _recarregar(self.client)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            resposta = self.client.post("/area/plano/", {"plano": "padrao"})
        self.assertEqual(resposta.status_code, 302)
        conta.refresh_from_db()
        self.assertEqual(conta.plano, Conta.PLANO_PADRAO)
        self.assertEqual(saldo_credito(conta), 10)
        self.assertEqual(Credito.objects.filter(conta=conta).count(), 1)

    def test_free_reload_writes_nothing_and_asks_for_a_plan(self):
        aberta = _criar(email="aberta@exemplo.com")
        _entrar(self.client, aberta)
        resposta = self.client.post("/area/credito/")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta["Location"], "/area/")
        self.assertEqual(Credito.objects.count(), 0)
        area = self.client.get("/area/")
        self.assertContains(area, AVISO)
        self.assertNotContains(area, ">Recarregar<")
        self.assertNotContains(area, 'action="/area/credito/"')
        aberta.refresh_from_db()
        self.assertEqual(aberta.plano, "")
        self.assertEqual(aberta.pesquisas_gratis_usadas, 0)

        bloqueada = _criar(email="bloqueada@exemplo.com")
        bloqueada.pesquisas_gratis_usadas = 10
        bloqueada.save(update_fields=["pesquisas_gratis_usadas"])
        _entrar(self.client, bloqueada)
        resposta = self.client.post("/area/credito/")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta["Location"], "/area/")
        self.assertEqual(Credito.objects.count(), 0)
        area = self.client.get("/area/")
        self.assertContains(area, AVISO)
        self.assertNotContains(area, ">Recarregar<")
        self.assertNotContains(area, 'action="/area/credito/"')
        bloqueada.refresh_from_db()
        self.assertEqual(bloqueada.plano, "")
        self.assertEqual(bloqueada.pesquisas_gratis_usadas, 10)

    def test_free_account_never_spends_credit(self):
        conta = _criar(email="gratis@exemplo.com")
        Credito.objects.create(conta=conta, preco=PRECO, restante=10)
        with patch("django.utils.timezone.now", return_value=conta.criada_em):
            self.assertTrue(aceitar_pesquisa(conta))
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 1)
        self.assertEqual(conta.plano, "")
        self.assertEqual(saldo_credito(conta), 10)
        self.assertEqual(Credito.objects.get(conta=conta).restante, 10)

    def test_empty_month_and_balance_refuse_a_search_and_show_results(self):
        conta = _criar(email="vazio@exemplo.com")
        _ativar(conta, Conta.PLANO_PADRAO)
        _definir_usadas(conta, 30, date(2026, 1, 1))
        _entrar(self.client, conta)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            self.assertFalse(aceitar_pesquisa(conta))
            self.assertFalse(pode_pesquisar(conta))
            self.assertTrue(pode_favoritar(conta))
            self.assertTrue(pode_configurar_alerta(conta))
            area = self.client.get("/area/")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_mes_usadas, 30)
        self.assertEqual(saldo_credito(conta), 0)
        self.assertEqual(Credito.objects.filter(conta=conta).count(), 0)
        self.assertContains(area, "Resultados")
        self.assertContains(area, "0 créditos")
        self.assertContains(area, ">Recarregar<")
        self.assertNotContains(area, "<li>")

    def test_paid_area_shows_one_credit_and_get_does_not_reload(self):
        conta = _criar(email="um@exemplo.com")
        _ativar(conta, Conta.PLANO_PADRAO)
        _entrar(self.client, conta)
        negado = self.client.get("/area/credito/")
        self.assertEqual(negado.status_code, 405)
        self.assertEqual(Credito.objects.filter(conta=conta).count(), 0)
        Credito.objects.create(conta=conta, preco=PRECO, restante=1)
        with patch("django.utils.timezone.now", return_value=JANEIRO):
            area = self.client.get("/area/")
        self.assertContains(area, "1 crédito")
        self.assertNotContains(area, "1 créditos")
        self.assertContains(area, 'action="/area/credito/"')


class MigracaoCreditoTests(TestCase):
    def test_migration_isolates_only_the_credit_table(self):
        texto = Path("contas/migrations/0005_credito.py").read_text(encoding="utf-8")
        self.assertIn("ENABLE ROW LEVEL SECURITY", texto)
        self.assertIn("FORCE ROW LEVEL SECURITY", texto)
        self.assertIn("conta_isola", texto)
        self.assertIn("public.contas_credito", texto)
        self.assertNotIn("contas_conta", texto)
        self.assertIn("rondimob_web", texto)
        self.assertIn("rondimob_worker", texto)
        self.assertIn('vendor != "postgresql"', texto)
