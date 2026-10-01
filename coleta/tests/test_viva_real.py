import inspect
import io
import json
import socket
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.apps import apps
from django.conf import settings
from django.test import TestCase

from anuncios.models import Anuncio, Preco
from coleta.models import Falha
from coleta.tasks import FIXTURE, FIXTURE_VIVA_REAL, coletar_viva_real, coletar_zap
from contas.models import Conta, Credito

ROOT = Path(__file__).resolve().parents[2]
SENHA = "senha-segura"
URL_ZAP = "https://exemplo.invalid/anuncio/zap-exemplo-1"


def _fixture_viva():
    return json.loads(FIXTURE_VIVA_REAL.read_text(encoding="utf-8"))


def _fixture_zap():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _linhas(saida):
    return [linha for linha in saida.getvalue().splitlines() if linha.strip()]


class VivaRealTests(TestCase):
    def test_fixture_grava_um_anuncio_e_um_preco(self):
        bruto = _fixture_viva()
        self.assertEqual(bruto["preco"], "650 mil")
        self.assertNotEqual(bruto["id"], "zap-exemplo-1")
        self.assertNotEqual(bruto["url"], URL_ZAP)

        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/area/").status_code, 302)
        self.assertEqual(Anuncio.objects.count(), 0)

        saida = io.StringIO()
        with redirect_stdout(saida):
            gravados = coletar_viva_real()

        self.assertEqual(gravados, 1)
        self.assertEqual(_linhas(saida), ["coleta viva-real gravou 1"])
        self.assertEqual(Anuncio.objects.count(), 1)
        self.assertEqual(Preco.objects.count(), 1)
        self.assertEqual(Falha.objects.count(), 0)
        anuncio = Anuncio.objects.get()
        preco = Preco.objects.get()
        self.assertEqual(anuncio.fonte, "viva-real")
        self.assertEqual(anuncio.identificador_externo, "viva-real-exemplo-1")
        self.assertEqual(
            anuncio.url,
            "https://exemplo.invalid/anuncio/viva-real-exemplo-1",
        )
        self.assertEqual(anuncio.preco, Decimal("650000.00"))
        self.assertEqual(anuncio.area, Decimal("72"))
        self.assertEqual(anuncio.quartos, 3)
        self.assertEqual(anuncio.banheiros, 2)
        self.assertEqual(anuncio.vagas, 1)
        self.assertEqual(anuncio.cidade, "são bernardo do campo")
        self.assertEqual(anuncio.bairro, "centro")
        self.assertEqual(anuncio.tipo, "casa")
        self.assertEqual(anuncio.imobiliaria, "imobiliária beta")
        self.assertEqual(anuncio.titulo, "Casa no Centro")
        self.assertEqual(anuncio.endereco, "Rua Gravada, 20")
        self.assertEqual(
            anuncio.descricao,
            "Anúncio gravado a partir do arquivo de exemplo da Viva Real.",
        )
        self.assertEqual(anuncio.coletado_em.utcoffset(), timedelta(0))
        self.assertEqual(preco.valor, Decimal("650000.00"))
        self.assertEqual(preco.anuncio, anuncio)
        self.assertEqual(self.client.get("/").status_code, 200)
        for relativo in (
            "contas/views.py",
            "radares/views.py",
            "config/urls.py",
            "contas/cota.py",
        ):
            self.assertNotIn(
                "coletar_viva_real",
                (ROOT / relativo).read_text(encoding="utf-8"),
            )

    def test_payload_sem_url_grava_falha_e_nenhum_anuncio(self):
        payload = _fixture_viva()
        payload["url"] = "  "

        saida = io.StringIO()
        with redirect_stdout(saida):
            resultado = coletar_viva_real(payload)

        self.assertIsNone(resultado)
        self.assertEqual(Anuncio.objects.count(), 0)
        self.assertEqual(Preco.objects.count(), 0)
        falha = Falha.objects.get()
        self.assertEqual(falha.fonte, "viva-real")
        self.assertEqual(falha.mensagem, "payload sem url")
        self.assertEqual(_linhas(saida), ["coleta viva-real falha: payload sem url"])

    def test_mesmo_preco_move_instante_e_preco_novo_abre_linha(self):
        payload = _fixture_viva()
        primeiro = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
        segundo = datetime(2026, 10, 1, 13, 0, tzinfo=timezone.utc)
        terceiro = datetime(2026, 10, 1, 14, 0, tzinfo=timezone.utc)
        instantes = [primeiro, segundo, terceiro]

        def agora(tz=None):
            return instantes.pop(0)

        with patch("anuncios.gravar.datetime") as relogio:
            relogio.now.side_effect = agora
            self.assertEqual(coletar_viva_real(payload), 1)
            payload["preco"] = "R$ 650.000"
            self.assertEqual(coletar_viva_real(payload), 1)
            anuncio = Anuncio.objects.get()
            self.assertEqual(Preco.objects.count(), 1)
            self.assertEqual(anuncio.preco, Decimal("650000.00"))
            self.assertEqual(anuncio.coletado_em, segundo)
            self.assertEqual(Preco.objects.get().coletado_em, primeiro)
            self.assertEqual(Preco.objects.get().valor, Decimal("650000.00"))
            payload["preco"] = "700000"
            self.assertEqual(coletar_viva_real(payload), 1)

        anuncio.refresh_from_db()
        self.assertEqual(Anuncio.objects.count(), 1)
        self.assertEqual(anuncio.preco, Decimal("700000.00"))
        self.assertEqual(Preco.objects.count(), 2)
        self.assertEqual(
            set(Preco.objects.values_list("valor", flat=True)),
            {Decimal("650000.00"), Decimal("700000.00")},
        )

    def test_zap_falha_primeiro_e_viva_real_grava(self):
        payload = _fixture_zap()
        payload["url"] = ""

        saida = io.StringIO()
        with redirect_stdout(saida):
            resultado_zap = coletar_zap(payload)
            resultado_viva = coletar_viva_real()

        self.assertIsNone(resultado_zap)
        self.assertEqual(resultado_viva, 1)
        self.assertFalse(Anuncio.objects.filter(fonte="zap").exists())
        anuncio = Anuncio.objects.get()
        self.assertEqual(anuncio.fonte, "viva-real")
        self.assertEqual(anuncio.identificador_externo, "viva-real-exemplo-1")
        self.assertEqual(Falha.objects.get().fonte, "zap")
        self.assertEqual(
            _linhas(saida),
            [
                "coleta zap falha: payload sem url",
                "coleta viva-real gravou 1",
            ],
        )
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_viva_real_falha_primeiro_e_zap_grava(self):
        payload = _fixture_viva()
        payload["url"] = ""

        saida = io.StringIO()
        with redirect_stdout(saida):
            resultado_viva = coletar_viva_real(payload)
            resultado_zap = coletar_zap()

        self.assertIsNone(resultado_viva)
        self.assertEqual(resultado_zap, 1)
        self.assertFalse(Anuncio.objects.filter(fonte="viva-real").exists())
        anuncio = Anuncio.objects.get()
        self.assertEqual(anuncio.fonte, "zap")
        self.assertEqual(anuncio.identificador_externo, "zap-exemplo-1")
        self.assertEqual(Falha.objects.get().fonte, "viva-real")
        self.assertEqual(
            _linhas(saida),
            [
                "coleta viva-real falha: payload sem url",
                "coleta zap gravou 1",
            ],
        )
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_falha_de_uma_fonte_nao_apaga_a_outra(self):
        self.assertEqual(coletar_viva_real(), 1)
        self.assertEqual(coletar_zap(), 1)
        ruim_zap = _fixture_zap()
        ruim_zap["url"] = ""
        ruim_viva = _fixture_viva()
        ruim_viva["url"] = ""

        with redirect_stdout(io.StringIO()):
            self.assertIsNone(coletar_zap(ruim_zap))
        self.assertEqual(Anuncio.objects.filter(fonte="viva-real").count(), 1)
        self.assertEqual(Anuncio.objects.filter(fonte="zap").count(), 1)

        with redirect_stdout(io.StringIO()):
            self.assertIsNone(coletar_viva_real(ruim_viva))
        self.assertEqual(Anuncio.objects.filter(fonte="zap").count(), 1)
        self.assertEqual(Anuncio.objects.filter(fonte="viva-real").count(), 1)
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_mesmo_id_e_url_em_duas_fontes_criam_dois(self):
        zap = _fixture_zap()
        viva = _fixture_viva()
        zap["id"] = viva["id"] = "compartilhado-1"
        zap["url"] = viva["url"] = "https://exemplo.invalid/compartilhado"

        self.assertEqual(coletar_zap(zap), 1)
        self.assertEqual(coletar_viva_real(viva), 1)

        self.assertEqual(Anuncio.objects.count(), 2)
        self.assertEqual(
            set(
                Anuncio.objects.values_list(
                    "fonte",
                    "identificador_externo",
                    "url",
                )
            ),
            {
                ("zap", "compartilhado-1", "https://exemplo.invalid/compartilhado"),
                (
                    "viva-real",
                    "compartilhado-1",
                    "https://exemplo.invalid/compartilhado",
                ),
            },
        )

    def test_nao_gasta_cota_nem_escreve_visto(self):
        conta = Conta.objects.create_user(
            email="ana-viva@exemplo.com",
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

        self.assertEqual(coletar_viva_real(), 1)

        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 2)
        self.assertEqual(conta.pesquisas_mes_usadas, 3)
        self.assertEqual(conta.plano, Conta.PLANO_PADRAO)
        self.assertEqual(conta.creditos.get().restante, 4)
        nomes = {modelo.__name__ for modelo in apps.get_models()}
        self.assertNotIn("RadarVisto", nomes)
        tarefa = inspect.getsource(coletar_viva_real)
        self.assertNotIn("aceitar_pesquisa", tarefa)
        self.assertNotIn("cota", tarefa)
        self.assertNotIn("RadarVisto", tarefa)
        self.assertNotIn("coletar_zap", tarefa)
        self.assertNotIn("coletar_viva_real", inspect.getsource(coletar_zap))

    def test_sem_redis_e_sem_rede(self):
        def recusar(*args, **kwargs):
            raise AssertionError("a coleta abriu um socket")

        with (
            patch.object(socket, "socket", side_effect=recusar),
            patch.object(socket, "create_connection", side_effect=recusar),
        ):
            self.assertEqual(coletar_viva_real(), 1)
        self.assertEqual(Anuncio.objects.get().fonte, "viva-real")
        codigo = "\n".join(
            (
                (ROOT / "coleta" / "parser.py").read_text(encoding="utf-8"),
                (ROOT / "coleta" / "tasks.py").read_text(encoding="utf-8"),
            )
        )
        for termo in ("urlopen", "import requests", "import httpx", "import socket"):
            self.assertNotIn(termo, codigo)

    def test_fila_viva_real(self):
        from config.celery import app

        self.assertEqual(settings.CELERY_BROKER_URL, "redis://localhost:6379/0")
        self.assertEqual(
            settings.CELERY_TASK_ROUTES["coleta.tasks.coletar_viva_real"],
            {"queue": "viva-real"},
        )
        app.loader.import_default_modules()
        tarefa = app.tasks["coleta.tasks.coletar_viva_real"]
        self.assertEqual(tarefa.queue, "viva-real")
        self.assertEqual(tarefa.name, "coleta.tasks.coletar_viva_real")
