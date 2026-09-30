from datetime import date
from decimal import Decimal

from django.test import TestCase

from contas.cota import (
    pode_configurar_alerta,
    pode_favoritar,
    pode_pesquisar,
    saldo_credito,
)
from contas.models import Conta, Credito
from radares.models import Radar

SENHA = "senha-segura"
MENSAGEM_CIDADE = (
    "Informe Santo André, São Bernardo do Campo, São Caetano do Sul ou Diadema."
)
ROTULO = "Santo André · apartamento · alfa"
EDICAO = {
    "imobiliaria": "Beta",
    "cidade": "Santo André",
    "bairro": "Centro",
    "tipo": "Casa",
    "preco_minimo": "100000",
    "preco_maximo": "200000",
    "area_minima": "40",
    "area_maxima": "80",
    "quartos_minimos": "3",
    "vagas_minimas": "2",
}
ROTULO_EDITADO = "Santo André · casa · beta"


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


def _radar(conta, **kwargs):
    dados = {
        "conta": conta,
        "imobiliaria": "alfa",
        "cidade": "Santo André",
        "bairro": "",
        "tipo": "apartamento",
        "preco_minimo": Decimal("300000"),
        "preco_maximo": Decimal("800000"),
        "area_minima": Decimal("60"),
        "quartos_minimos": 2,
        "vagas_minimas": 1,
    }
    dados.update(kwargs)
    return Radar.objects.create(**dados)


def _foto(radar):
    radar.refresh_from_db()
    return (
        radar.id,
        radar.conta_id,
        radar.imobiliaria,
        radar.cidade,
        radar.bairro,
        radar.tipo,
        radar.preco_minimo,
        radar.preco_maximo,
        radar.area_minima,
        radar.area_maxima,
        radar.quartos_minimos,
        radar.vagas_minimas,
        radar.criado_em,
    )


def _url(radar):
    return f"/area/radares/{radar.id}/"


class EditarRadarTests(TestCase):
    def test_edit_updates_filters_and_the_label_without_spending(self):
        conta = _criar()
        conta.pesquisas_gratis_usadas = 3
        conta.pesquisas_mes_usadas = 2
        conta.mes_da_cota = date(2026, 9, 1)
        conta.save(
            update_fields=[
                "pesquisas_gratis_usadas",
                "pesquisas_mes_usadas",
                "mes_da_cota",
            ]
        )
        Credito.objects.create(conta=conta, preco=Decimal("47.00"), restante=4)
        radar = _radar(conta)
        url = _url(radar)
        antes = _foto(radar)

        anonima = self.client.post(url, EDICAO)
        self.assertEqual(anonima.status_code, 302)
        self.assertEqual(anonima["Location"], "/entrar/")
        self.assertEqual(_foto(radar), antes)
        self.assertEqual(Radar.objects.count(), 1)

        _entrar(self.client, conta)
        criar = self.client.get("/area/radares/novo/")
        self.assertContains(criar, "Novo radar")
        self.assertContains(criar, 'action="/area/radares/novo/"')

        lista = self.client.get("/area/")
        self.assertContains(lista, f'href="{url}"')
        self.assertContains(lista, ROTULO)
        self.assertContains(lista, "Novo radar")

        pagina = self.client.get(url)
        self.assertEqual(pagina.status_code, 200)
        self.assertContains(pagina, "Editar radar")
        self.assertContains(pagina, f'action="{url}"')
        self.assertContains(pagina, 'value="Santo André"')
        self.assertEqual(_foto(radar), antes)

        resposta = self.client.post(url, EDICAO)
        self.assertRedirects(resposta, "/area/")
        self.assertEqual(Radar.objects.count(), 1)
        radar.refresh_from_db()
        self.assertEqual(radar.id, antes[0])
        self.assertEqual(radar.conta, conta)
        self.assertEqual(radar.imobiliaria, "beta")
        self.assertEqual(radar.cidade, "Santo André")
        self.assertEqual(radar.bairro, "centro")
        self.assertEqual(radar.tipo, "casa")
        self.assertEqual(radar.preco_minimo, Decimal("100000"))
        self.assertEqual(radar.preco_maximo, Decimal("200000"))
        self.assertEqual(radar.area_minima, Decimal("40"))
        self.assertEqual(radar.area_maxima, Decimal("80"))
        self.assertEqual(radar.quartos_minimos, 3)
        self.assertEqual(radar.vagas_minimas, 2)
        self.assertEqual(radar.rotulo, ROTULO_EDITADO)

        area = self.client.get("/area/")
        self.assertContains(area, ROTULO_EDITADO)
        self.assertContains(area, f'href="{url}"')
        self.assertNotContains(area, ROTULO)
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 3)
        self.assertEqual(conta.pesquisas_mes_usadas, 2)
        self.assertEqual(saldo_credito(conta), 4)
        self.assertEqual(Credito.objects.get(conta=conta).restante, 4)

    def test_city_inside_abcd_updates_the_same_radar(self):
        conta = _criar()
        radar = _radar(conta)
        identificador = radar.id
        _entrar(self.client, conta)
        resposta = self.client.post(
            _url(radar),
            {**EDICAO, "cidade": "Diadema"},
        )
        self.assertRedirects(resposta, "/area/")
        self.assertEqual(Radar.objects.count(), 1)
        radar.refresh_from_db()
        self.assertEqual(radar.id, identificador)
        self.assertEqual(radar.cidade, "Diadema")

    def test_city_outside_abcd_keeps_every_stored_column(self):
        conta = _criar()
        radar = _radar(conta)
        antes = _foto(radar)
        _entrar(self.client, conta)
        resposta = self.client.post(
            _url(radar),
            {
                "imobiliaria": "Beta",
                "cidade": "São Paulo",
                "bairro": "Vila",
                "tipo": "casa",
                "preco_minimo": "1",
                "preco_maximo": "2",
                "area_minima": "3",
                "area_maxima": "4",
                "quartos_minimos": "9",
                "vagas_minimas": "8",
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Editar radar")
        self.assertContains(resposta, f'action="{_url(radar)}"')
        self.assertContains(resposta, 'name="cidade"')
        self.assertContains(resposta, MENSAGEM_CIDADE)
        self.assertEqual(_foto(radar), antes)
        self.assertEqual(Radar.objects.count(), 1)

    def test_other_account_gets_404_and_the_row_stays(self):
        dona = _criar(email="dona@exemplo.com")
        radar = _radar(dona)
        antes = _foto(radar)
        outra = _criar(email="outra@exemplo.com", nome="Bia Costa")
        _entrar(self.client, outra)
        resposta = self.client.post(
            _url(radar),
            {**EDICAO, "cidade": "Diadema"},
        )
        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(_foto(radar), antes)
        self.assertEqual(Radar.objects.count(), 1)

    def test_closed_trial_still_updates_and_keeps_the_gates_closed(self):
        conta = _criar()
        radar = _radar(conta)
        conta.pesquisas_gratis_usadas = 10
        conta.save(update_fields=["pesquisas_gratis_usadas"])
        self.assertFalse(pode_pesquisar(conta))
        self.assertFalse(pode_favoritar(conta))
        self.assertFalse(pode_configurar_alerta(conta))
        _entrar(self.client, conta)

        resposta = self.client.post(_url(radar), {**EDICAO, "bairro": "Vila"})
        self.assertRedirects(resposta, "/area/")
        self.assertEqual(Radar.objects.count(), 1)
        radar.refresh_from_db()
        self.assertEqual(radar.bairro, "vila")
        self.assertEqual(radar.cidade, "Santo André")
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 10)
        self.assertEqual(conta.pesquisas_mes_usadas, 0)
        self.assertEqual(saldo_credito(conta), 0)
        self.assertFalse(pode_pesquisar(conta))
        self.assertFalse(pode_favoritar(conta))
        self.assertFalse(pode_configurar_alerta(conta))
