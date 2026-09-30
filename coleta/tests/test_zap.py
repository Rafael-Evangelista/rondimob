import inspect
import io
import json
import socket
import uuid
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import celery
from django.apps import apps
from django.conf import settings
from django.test import TestCase

from anuncios.models import Anuncio, Preco
from coleta.models import Falha
from coleta.tasks import FIXTURE, coletar_zap
from contas.models import Conta, Credito

ROOT = Path(__file__).resolve().parents[2]
SENHA = "senha-segura"


def _fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _linhas(saida):
    return [linha for linha in saida.getvalue().splitlines() if linha.strip()]


class ZapTests(TestCase):
    def test_fixture_grava_um_anuncio_e_um_preco(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/area/").status_code, 302)
        self.assertEqual(Anuncio.objects.count(), 0)

        saida = io.StringIO()
        with redirect_stdout(saida):
            gravados = coletar_zap()

        self.assertEqual(gravados, 1)
        self.assertEqual(_linhas(saida), ["coleta zap gravou 1"])
        self.assertEqual(Anuncio.objects.count(), 1)
        self.assertEqual(Preco.objects.count(), 1)
        self.assertEqual(Falha.objects.count(), 0)
        anuncio = Anuncio.objects.get()
        preco = Preco.objects.get()
        self.assertIsInstance(anuncio.id, uuid.UUID)
        self.assertEqual(anuncio.fonte, "zap")
        self.assertEqual(anuncio.identificador_externo, "zap-exemplo-1")
        self.assertEqual(anuncio.url, "https://exemplo.invalid/anuncio/zap-exemplo-1")
        self.assertEqual(anuncio.preco, Decimal("650000.00"))
        self.assertEqual(anuncio.area, Decimal("60"))
        self.assertEqual(anuncio.quartos, 2)
        self.assertEqual(anuncio.banheiros, 1)
        self.assertEqual(anuncio.vagas, 1)
        self.assertEqual(anuncio.cidade, "santo andré")
        self.assertEqual(anuncio.bairro, "centro")
        self.assertEqual(anuncio.tipo, "apartamento")
        self.assertEqual(anuncio.imobiliaria, "imobiliária alfa")
        self.assertEqual(anuncio.titulo, "Apartamento no Centro")
        self.assertEqual(anuncio.coletado_em.utcoffset(), timedelta(0))
        self.assertEqual(preco.valor, Decimal("650000.00"))
        self.assertEqual(preco.anuncio, anuncio)
        self.assertNotIn("conta", {campo.name for campo in Anuncio._meta.fields})
        self.assertNotIn("conta", {campo.name for campo in Preco._meta.fields})

    def test_payload_sem_url_grava_falha_e_nenhum_anuncio(self):
        payload = _fixture()
        payload["url"] = "  "

        saida = io.StringIO()
        with redirect_stdout(saida):
            resultado = coletar_zap(payload)

        self.assertIsNone(resultado)
        self.assertEqual(Anuncio.objects.count(), 0)
        self.assertEqual(Preco.objects.count(), 0)
        self.assertEqual(Falha.objects.get().mensagem, "payload sem url")
        self.assertEqual(_linhas(saida), ["coleta zap falha: payload sem url"])

    def test_tres_textos_de_preco_sao_o_mesmo_numero(self):
        base = _fixture()
        for indice, texto in enumerate(("R$ 650.000", "650 mil", "650000")):
            item = dict(base)
            item["id"] = f"preco-{indice}"
            item["url"] = f"https://exemplo.invalid/preco-{indice}"
            item["preco"] = texto
            self.assertEqual(coletar_zap(item), 1)
        self.assertEqual(
            set(Anuncio.objects.values_list("preco", flat=True)),
            {Decimal("650000.00")},
        )
        self.assertEqual(Preco.objects.count(), 3)

    def test_mesmo_preco_nao_duplica_e_move_o_instante(self):
        payload = _fixture()
        payload["preco"] = "650 mil"
        primeiro = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
        segundo = datetime(2026, 9, 30, 13, 0, tzinfo=timezone.utc)
        instantes = [primeiro, segundo]

        def agora(tz=None):
            return instantes.pop(0)

        with patch("anuncios.gravar.datetime") as relogio:
            relogio.now.side_effect = agora
            coletar_zap(payload)
            payload["preco"] = "650000"
            payload["cidade"] = "Diadema"
            coletar_zap(payload)

        anuncio = Anuncio.objects.get()
        self.assertEqual(Anuncio.objects.count(), 1)
        self.assertEqual(Preco.objects.count(), 1)
        self.assertEqual(anuncio.preco, Decimal("650000.00"))
        self.assertEqual(anuncio.coletado_em, segundo)
        self.assertEqual(anuncio.cidade, "santo andré")
        self.assertEqual(Preco.objects.get().coletado_em, primeiro)
        self.assertEqual(Preco.objects.get().valor, Decimal("650000.00"))

    def test_preco_diferente_abre_outra_linha(self):
        payload = _fixture()
        coletar_zap(payload)
        payload["preco"] = "700000"
        coletar_zap(payload)

        anuncio = Anuncio.objects.get()
        self.assertEqual(anuncio.preco, Decimal("700000.00"))
        self.assertEqual(
            set(Preco.objects.values_list("valor", flat=True)),
            {Decimal("650000.00"), Decimal("700000.00")},
        )

    def test_sem_id_a_url_e_a_chave(self):
        payload = _fixture()
        del payload["id"]
        payload["url"] = "https://exemplo.invalid/sem-id"
        coletar_zap(payload)
        payload["titulo"] = "Outro título"
        coletar_zap(payload)

        anuncio = Anuncio.objects.get()
        self.assertEqual(anuncio.identificador_externo, "")
        self.assertEqual(anuncio.url, "https://exemplo.invalid/sem-id")
        self.assertEqual(anuncio.titulo, "Apartamento no Centro")
        self.assertEqual(Preco.objects.count(), 1)

    def test_nao_gasta_cota_nem_escreve_visto(self):
        conta = Conta.objects.create_user(
            email="ana-coleta@exemplo.com",
            password=SENHA,
            tipo=Conta.TIPO_CORRETOR,
            nome="Ana Lima",
        )
        conta.plano = Conta.PLANO_PADRAO
        conta.pesquisas_gratis_usadas = 2
        conta.pesquisas_mes_usadas = 3
        conta.save()
        Credito.objects.create(
            conta=conta,
            preco=Decimal("47.00"),
            restante=4,
        )

        self.assertEqual(coletar_zap(), 1)

        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 2)
        self.assertEqual(conta.pesquisas_mes_usadas, 3)
        self.assertEqual(conta.plano, Conta.PLANO_PADRAO)
        self.assertEqual(conta.creditos.get().restante, 4)
        nomes = {modelo.__name__ for modelo in apps.get_models()}
        self.assertNotIn("RadarVisto", nomes)
        tarefa = inspect.getsource(coletar_zap)
        self.assertNotIn("aceitar_pesquisa", tarefa)
        self.assertNotIn("cota", tarefa)
        self.assertNotIn("RadarVisto", tarefa)

    def test_erro_do_parser_grava_falha_e_uma_linha(self):
        payload = _fixture()
        payload["preco"] = "não é preço"

        saida = io.StringIO()
        with redirect_stdout(saida):
            resultado = coletar_zap(payload)

        self.assertIsNone(resultado)
        self.assertEqual(Anuncio.objects.count(), 0)
        self.assertEqual(Falha.objects.get().fonte, "zap")
        self.assertEqual(Falha.objects.get().mensagem, "preço inválido")
        self.assertEqual(_linhas(saida), ["coleta zap falha: preço inválido"])

    def test_erro_nao_deixa_anuncio_pela_metade(self):
        saida = io.StringIO()
        with patch(
            "anuncios.gravar.Preco.objects.create",
            side_effect=RuntimeError("quebra"),
        ):
            with redirect_stdout(saida):
                resultado = coletar_zap()

        self.assertIsNone(resultado)
        self.assertEqual(Anuncio.objects.count(), 0)
        self.assertEqual(Preco.objects.count(), 0)
        self.assertEqual(Falha.objects.get().mensagem, "quebra")
        self.assertEqual(_linhas(saida), ["coleta zap falha: quebra"])

    def test_nao_abre_socket_nem_sai_de_uma_view(self):
        def recusar(*args, **kwargs):
            raise AssertionError("a coleta abriu um socket")

        with (
            patch.object(socket, "socket", side_effect=recusar),
            patch.object(socket, "create_connection", side_effect=recusar),
        ):
            self.assertEqual(coletar_zap(), 1)
        for relativo in (
            "contas/views.py",
            "radares/views.py",
            "config/urls.py",
            "contas/cota.py",
        ):
            self.assertNotIn("coletar_zap", (ROOT / relativo).read_text(encoding="utf-8"))
        codigo = "\n".join(
            (
                (ROOT / "coleta" / "parser.py").read_text(encoding="utf-8"),
                (ROOT / "coleta" / "tasks.py").read_text(encoding="utf-8"),
            )
        )
        for termo in ("urlopen", "import requests", "import httpx", "import socket"):
            self.assertNotIn(termo, codigo)

    def test_fila_zap_broker_e_celery(self):
        from config.celery import app

        self.assertEqual(celery.__version__, "5.6.3")
        self.assertEqual(settings.CELERY_BROKER_URL, "redis://localhost:6379/0")
        self.assertEqual(
            settings.CELERY_TASK_ROUTES["coleta.tasks.coletar_zap"],
            {"queue": "zap"},
        )
        app.loader.import_default_modules()
        tarefa = app.tasks["coleta.tasks.coletar_zap"]
        self.assertEqual(tarefa.queue, "zap")
        self.assertIn("anuncios", settings.INSTALLED_APPS)
        self.assertIn("coleta", settings.INSTALLED_APPS)
