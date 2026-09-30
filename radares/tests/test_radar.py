import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.test import TestCase

from contas.cota import (
    nomes_de_radar,
    pode_configurar_alerta,
    pode_favoritar,
    pode_pesquisar,
    saldo_credito,
)
from contas.models import Conta, Credito
from radares.models import Radar

SENHA = "senha-segura"
EXEMPLO = {
    "imobiliaria": "Alfa",
    "cidade": "Santo André",
    "bairro": "",
    "tipo": "apartamento",
    "preco_minimo": "300000",
    "preco_maximo": "800000",
    "area_minima": "60",
    "area_maxima": "",
    "quartos_minimos": "2",
    "vagas_minimas": "1",
}
ROTULO = "Santo André · apartamento · alfa"


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


class RadarFormTests(TestCase):
    def test_example_saves_filters_lists_the_label_and_does_not_spend(self):
        anonima = self.client.post("/area/radares/novo/", EXEMPLO)
        self.assertEqual(anonima.status_code, 302)
        self.assertEqual(anonima["Location"], "/entrar/")
        self.assertEqual(Radar.objects.count(), 0)

        conta = _criar()
        _entrar(self.client, conta)
        formulario = self.client.get("/area/radares/novo/")
        self.assertEqual(formulario.status_code, 200)
        self.assertContains(formulario, 'action="/area/radares/novo/"')
        self.assertContains(formulario, 'name="cidade"')
        self.assertContains(formulario, 'name="imobiliaria"')

        resposta = self.client.post("/area/radares/novo/", EXEMPLO)
        self.assertRedirects(resposta, "/area/")
        self.assertEqual(Radar.objects.count(), 1)
        radar = Radar.objects.get()
        self.assertIsInstance(radar.id, uuid.UUID)
        self.assertEqual(radar.conta, conta)
        self.assertEqual(radar.imobiliaria, "alfa")
        self.assertEqual(radar.cidade, "Santo André")
        self.assertEqual(radar.bairro, "")
        self.assertEqual(radar.tipo, "apartamento")
        self.assertEqual(radar.preco_minimo, Decimal("300000"))
        self.assertEqual(radar.preco_maximo, Decimal("800000"))
        self.assertEqual(radar.area_minima, Decimal("60"))
        self.assertIsNone(radar.area_maxima)
        self.assertEqual(radar.quartos_minimos, 2)
        self.assertEqual(radar.vagas_minimas, 1)
        self.assertEqual(radar.rotulo, ROTULO)
        self.assertEqual(nomes_de_radar(conta), [ROTULO])

        area = self.client.get("/area/")
        self.assertContains(area, ROTULO)
        self.assertContains(area, "Novo radar")
        self.assertContains(area, 'href="/area/radares/novo/"')
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 0)
        self.assertEqual(conta.pesquisas_mes_usadas, 0)
        self.assertEqual(saldo_credito(conta), 0)

    def test_city_outside_abcd_or_blank_creates_nothing(self):
        conta = _criar()
        _entrar(self.client, conta)
        for cidade in ("São Paulo", ""):
            with self.subTest(cidade=cidade):
                resposta = self.client.post(
                    "/area/radares/novo/",
                    {**EXEMPLO, "cidade": cidade},
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, 'action="/area/radares/novo/"')
                self.assertContains(resposta, 'name="cidade"')
                self.assertEqual(Radar.objects.count(), 0)

    def test_second_radar_stays_in_the_list_without_spending(self):
        conta = _criar()
        _entrar(self.client, conta)
        primeiro = self.client.post("/area/radares/novo/", EXEMPLO)
        self.assertRedirects(primeiro, "/area/")
        segundo_rotulo = "Diadema · casa · beta"
        segundo = self.client.post(
            "/area/radares/novo/",
            {
                **EXEMPLO,
                "imobiliaria": "Beta",
                "cidade": "Diadema",
                "tipo": "casa",
            },
        )
        self.assertRedirects(segundo, "/area/")
        self.assertEqual(nomes_de_radar(conta), [ROTULO, segundo_rotulo])
        area = self.client.get("/area/")
        html = area.content.decode()
        self.assertLess(html.index(ROTULO), html.index(segundo_rotulo))
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 0)
        self.assertEqual(conta.pesquisas_mes_usadas, 0)
        self.assertEqual(saldo_credito(conta), 0)
        self.assertEqual(Radar.objects.filter(conta=conta).count(), 2)

    def test_closed_trial_still_creates_and_lists_the_radar(self):
        conta = _criar()
        conta.pesquisas_gratis_usadas = 10
        conta.save(update_fields=["pesquisas_gratis_usadas"])
        _entrar(self.client, conta)
        self.assertFalse(pode_pesquisar(conta))
        self.assertFalse(pode_favoritar(conta))
        self.assertFalse(pode_configurar_alerta(conta))

        resposta = self.client.post("/area/radares/novo/", EXEMPLO)
        self.assertRedirects(resposta, "/area/")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 10)
        self.assertEqual(conta.pesquisas_mes_usadas, 0)
        self.assertEqual(saldo_credito(conta), 0)
        self.assertFalse(pode_pesquisar(conta))
        self.assertFalse(pode_favoritar(conta))
        self.assertFalse(pode_configurar_alerta(conta))
        area = self.client.get("/area/")
        self.assertContains(area, ROTULO)
        self.assertContains(area, "Radares")
        self.assertContains(area, "R$ 97 por mês")
        self.assertContains(area, "Novo radar")

    def test_accent_and_case_store_the_canonical_city(self):
        conta = _criar()
        _entrar(self.client, conta)
        casos = (
            ("sAnTo AnDrÉ", "Santo André"),
            ("SÃO BERNARDO DO CAMPO", "São Bernardo do Campo"),
            ("sao caetano do sul", "São Caetano do Sul"),
            ("DIADEMA", "Diadema"),
        )
        for digitado, canonica in casos:
            with self.subTest(cidade=digitado):
                resposta = self.client.post(
                    "/area/radares/novo/",
                    {
                        "imobiliaria": "  Alfa  ",
                        "cidade": digitado,
                        "bairro": "  Centro  ",
                        "tipo": " Apartamento ",
                    },
                )
                self.assertRedirects(resposta, "/area/")
        gravadas = list(
            Radar.objects.filter(conta=conta).order_by("criado_em").values_list(
                "cidade", "imobiliaria", "bairro", "tipo"
            )
        )
        self.assertEqual(
            gravadas,
            [
                ("Santo André", "alfa", "centro", "apartamento"),
                ("São Bernardo do Campo", "alfa", "centro", "apartamento"),
                ("São Caetano do Sul", "alfa", "centro", "apartamento"),
                ("Diadema", "alfa", "centro", "apartamento"),
            ],
        )

    def test_max_below_min_creates_nothing(self):
        conta = _criar()
        _entrar(self.client, conta)
        casos = (
            {"preco_minimo": "800000", "preco_maximo": "300000"},
            {"area_minima": "90", "area_maxima": "60"},
        )
        for ajuste in casos:
            with self.subTest(ajuste=ajuste):
                resposta = self.client.post(
                    "/area/radares/novo/",
                    {**EXEMPLO, **ajuste},
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, 'name="cidade"')
                self.assertEqual(Radar.objects.count(), 0)

    def test_only_city_is_required_and_blanks_are_skipped_in_the_label(self):
        conta = _criar()
        _entrar(self.client, conta)
        resposta = self.client.post("/area/radares/novo/", {"cidade": "diadema"})
        self.assertRedirects(resposta, "/area/")
        radar = Radar.objects.get()
        self.assertEqual(radar.cidade, "Diadema")
        self.assertEqual(radar.imobiliaria, "")
        self.assertEqual(radar.bairro, "")
        self.assertEqual(radar.tipo, "")
        self.assertIsNone(radar.preco_minimo)
        self.assertIsNone(radar.preco_maximo)
        self.assertIsNone(radar.area_minima)
        self.assertIsNone(radar.area_maxima)
        self.assertIsNone(radar.quartos_minimos)
        self.assertIsNone(radar.vagas_minimas)
        self.assertEqual(radar.rotulo, "Diadema")
        self.assertContains(self.client.get("/area/"), "Diadema")

    def test_paid_area_lists_the_radar_without_spending_month_or_credit(self):
        conta = _criar(email="paga@exemplo.com")
        conta.plano = Conta.PLANO_PADRAO
        conta.pesquisas_mes_usadas = 4
        conta.mes_da_cota = date(2026, 9, 1)
        conta.save(
            update_fields=["plano", "pesquisas_mes_usadas", "mes_da_cota"]
        )
        Credito.objects.create(
            conta=conta,
            preco=Decimal("47.00"),
            restante=7,
        )
        _entrar(self.client, conta)
        resposta = self.client.post("/area/radares/novo/", EXEMPLO)
        self.assertRedirects(resposta, "/area/")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 0)
        self.assertEqual(conta.pesquisas_mes_usadas, 4)
        self.assertEqual(saldo_credito(conta), 7)
        self.assertEqual(Credito.objects.get(conta=conta).restante, 7)
        area = self.client.get("/area/")
        self.assertContains(area, ROTULO)
        self.assertContains(area, "Novo radar")
        self.assertContains(area, "Padrão")


class MigracaoRadarTests(TestCase):
    def test_migration_isolates_only_the_radar_table(self):
        texto = Path("radares/migrations/0001_initial.py").read_text(encoding="utf-8")
        self.assertIn("ENABLE ROW LEVEL SECURITY", texto)
        self.assertIn("FORCE ROW LEVEL SECURITY", texto)
        self.assertIn("conta_isola", texto)
        self.assertIn("public.radares_radar", texto)
        self.assertNotIn("contas_conta", texto)
        self.assertIn("rondimob_web", texto)
        self.assertIn("rondimob_worker", texto)
        self.assertIn('vendor != "postgresql"', texto)
        self.assertIn("uuid", texto)
