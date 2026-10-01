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
from coleta.tasks import (
    FIXTURE,
    FIXTURE_OLX,
    FIXTURE_VIVA_REAL,
    coletar_olx,
    coletar_viva_real,
    coletar_zap,
)
from contas.models import Conta, Credito

ROOT = Path(__file__).resolve().parents[2]
SENHA = "senha-segura"
URL_COMPARTILHADA = "https://exemplo.invalid/compartilhado"


def _fixture_olx():
    return json.loads(FIXTURE_OLX.read_text(encoding="utf-8"))


def _fixture_viva():
    return json.loads(FIXTURE_VIVA_REAL.read_text(encoding="utf-8"))


def _fixture_zap():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _linhas(saida):
    return [linha for linha in saida.getvalue().splitlines() if linha.strip()]


class OlxTests(TestCase):
    def test_fixture_grava_um_anuncio_e_um_preco(self):
        bruto = _fixture_olx()
        self.assertEqual(bruto["preco"], "R$ 650.000")
        self.assertNotEqual(bruto["id"], "zap-exemplo-1")
        self.assertNotEqual(bruto["id"], "viva-real-exemplo-1")
        self.assertNotEqual(
            bruto["url"],
            "https://exemplo.invalid/anuncio/zap-exemplo-1",
        )
        self.assertNotEqual(
            bruto["url"],
            "https://exemplo.invalid/anuncio/viva-real-exemplo-1",
        )

        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/area/").status_code, 302)
        self.assertEqual(Anuncio.objects.count(), 0)

        conta = Conta.objects.create_user(
            email="ana-pagina-olx@exemplo.com",
            password=SENHA,
            tipo=Conta.TIPO_CORRETOR,
            nome="Ana Lima",
        )
        entrada = self.client.post(
            "/entrar/",
            {"email": conta.email, "senha": SENHA},
        )
        self.assertEqual(entrada.status_code, 302)
        area = self.client.get("/area/")
        self.assertEqual(area.status_code, 200)
        radar = self.client.post(
            "/area/radares/novo/",
            {
                "cidade": "Santo André",
                "imobiliaria": "Alfa",
                "tipo": "apartamento",
                "preco_minimo": "300000",
                "preco_maximo": "800000",
                "area_minima": "60",
                "quartos_minimos": "2",
                "vagas_minimas": "1",
                "bairro": "",
                "area_maxima": "",
            },
        )
        self.assertEqual(radar.status_code, 302)
        self.assertEqual(Anuncio.objects.count(), 0)

        saida = io.StringIO()
        with redirect_stdout(saida):
            gravados = coletar_olx()

        self.assertEqual(gravados, 1)
        self.assertEqual(_linhas(saida), ["coleta olx gravou 1"])
        self.assertEqual(Anuncio.objects.count(), 1)
        self.assertEqual(Preco.objects.count(), 1)
        self.assertEqual(Falha.objects.count(), 0)
        anuncio = Anuncio.objects.get()
        preco = Preco.objects.get()
        self.assertEqual(anuncio.fonte, "olx")
        self.assertEqual(anuncio.identificador_externo, "olx-exemplo-1")
        self.assertEqual(
            anuncio.url,
            "https://exemplo.invalid/anuncio/olx-exemplo-1",
        )
        self.assertEqual(anuncio.preco, Decimal("650000.00"))
        self.assertEqual(anuncio.area, Decimal("85"))
        self.assertEqual(anuncio.quartos, 2)
        self.assertEqual(anuncio.banheiros, 1)
        self.assertEqual(anuncio.vagas, 2)
        self.assertEqual(anuncio.cidade, "são caetano do sul")
        self.assertEqual(anuncio.bairro, "fundação")
        self.assertEqual(anuncio.tipo, "apartamento")
        self.assertEqual(anuncio.imobiliaria, "imobiliária gama")
        self.assertEqual(anuncio.titulo, "Apartamento na Fundação")
        self.assertEqual(anuncio.endereco, "Rua Gravada, 30")
        self.assertEqual(
            anuncio.descricao,
            "Anúncio gravado a partir do arquivo de exemplo da OLX.",
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
                "coletar_olx",
                (ROOT / relativo).read_text(encoding="utf-8"),
            )

    def test_payload_sem_url_grava_falha_e_nenhum_anuncio(self):
        payload = _fixture_olx()
        payload["url"] = "  "

        saida = io.StringIO()
        with redirect_stdout(saida):
            resultado = coletar_olx(payload)

        self.assertIsNone(resultado)
        self.assertEqual(Anuncio.objects.count(), 0)
        self.assertEqual(Preco.objects.count(), 0)
        falha = Falha.objects.get()
        self.assertEqual(falha.fonte, "olx")
        self.assertEqual(falha.mensagem, "payload sem url")
        self.assertEqual(_linhas(saida), ["coleta olx falha: payload sem url"])

    def test_mesmo_preco_move_instante_e_preco_novo_abre_linha(self):
        payload = _fixture_olx()
        primeiro = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
        segundo = datetime(2026, 10, 1, 13, 0, tzinfo=timezone.utc)
        terceiro = datetime(2026, 10, 1, 14, 0, tzinfo=timezone.utc)
        instantes = [primeiro, segundo, terceiro]

        def agora(tz=None):
            return instantes.pop(0)

        with patch("anuncios.gravar.datetime") as relogio:
            relogio.now.side_effect = agora
            self.assertEqual(coletar_olx(payload), 1)
            payload["preco"] = "650 mil"
            self.assertEqual(coletar_olx(payload), 1)
            anuncio = Anuncio.objects.get()
            self.assertEqual(Preco.objects.count(), 1)
            self.assertEqual(anuncio.preco, Decimal("650000.00"))
            self.assertEqual(anuncio.coletado_em, segundo)
            self.assertEqual(Preco.objects.get().coletado_em, primeiro)
            self.assertEqual(Preco.objects.get().valor, Decimal("650000.00"))
            payload["preco"] = "700000"
            self.assertEqual(coletar_olx(payload), 1)

        anuncio.refresh_from_db()
        self.assertEqual(Anuncio.objects.count(), 1)
        self.assertEqual(anuncio.preco, Decimal("700000.00"))
        self.assertEqual(Preco.objects.count(), 2)
        self.assertEqual(
            set(Preco.objects.values_list("valor", flat=True)),
            {Decimal("650000.00"), Decimal("700000.00")},
        )

    def test_zap_e_viva_real_falham_e_olx_grava(self):
        zap = _fixture_zap()
        zap["url"] = ""
        viva = _fixture_viva()
        viva["url"] = ""

        saida = io.StringIO()
        with redirect_stdout(saida):
            resultado_zap = coletar_zap(zap)
            resultado_viva = coletar_viva_real(viva)
            resultado_olx = coletar_olx()

        self.assertIsNone(resultado_zap)
        self.assertIsNone(resultado_viva)
        self.assertEqual(resultado_olx, 1)
        self.assertFalse(Anuncio.objects.filter(fonte="zap").exists())
        self.assertFalse(Anuncio.objects.filter(fonte="viva-real").exists())
        anuncio = Anuncio.objects.get()
        self.assertEqual(anuncio.fonte, "olx")
        self.assertEqual(anuncio.identificador_externo, "olx-exemplo-1")
        self.assertEqual(
            set(Falha.objects.values_list("fonte", flat=True)),
            {"zap", "viva-real"},
        )
        self.assertEqual(Falha.objects.filter(fonte="zap").count(), 1)
        self.assertEqual(Falha.objects.filter(fonte="viva-real").count(), 1)
        self.assertEqual(
            _linhas(saida),
            [
                "coleta zap falha: payload sem url",
                "coleta viva-real falha: payload sem url",
                "coleta olx gravou 1",
            ],
        )
        self.assertEqual(self.client.get("/").status_code, 200)

        with redirect_stdout(io.StringIO()):
            self.assertIsNone(coletar_zap(zap))
            self.assertIsNone(coletar_viva_real(viva))
        self.assertEqual(Anuncio.objects.filter(fonte="olx").count(), 1)
        self.assertFalse(Anuncio.objects.filter(fonte="zap").exists())
        self.assertFalse(Anuncio.objects.filter(fonte="viva-real").exists())

    def test_olx_falha_e_as_outras_filas_gravam(self):
        ruim = _fixture_olx()
        ruim["url"] = ""

        saida = io.StringIO()
        with redirect_stdout(saida):
            resultado_olx = coletar_olx(ruim)
            resultado_zap = coletar_zap()
            resultado_viva = coletar_viva_real()

        self.assertIsNone(resultado_olx)
        self.assertEqual(resultado_zap, 1)
        self.assertEqual(resultado_viva, 1)
        self.assertFalse(Anuncio.objects.filter(fonte="olx").exists())
        self.assertEqual(Anuncio.objects.filter(fonte="zap").count(), 1)
        self.assertEqual(Anuncio.objects.filter(fonte="viva-real").count(), 1)
        self.assertEqual(Falha.objects.get().fonte, "olx")
        self.assertEqual(
            _linhas(saida),
            [
                "coleta olx falha: payload sem url",
                "coleta zap gravou 1",
                "coleta viva-real gravou 1",
            ],
        )
        self.assertEqual(self.client.get("/").status_code, 200)

        with redirect_stdout(io.StringIO()):
            self.assertIsNone(coletar_olx(ruim))
        self.assertEqual(Anuncio.objects.filter(fonte="zap").count(), 1)
        self.assertEqual(Anuncio.objects.filter(fonte="viva-real").count(), 1)
        self.assertFalse(Anuncio.objects.filter(fonte="olx").exists())
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_mesmo_id_e_url_em_tres_fontes_criam_tres(self):
        zap = _fixture_zap()
        viva = _fixture_viva()
        olx = _fixture_olx()
        zap["id"] = viva["id"] = olx["id"] = "compartilhado-1"
        zap["url"] = viva["url"] = olx["url"] = URL_COMPARTILHADA

        self.assertEqual(coletar_zap(zap), 1)
        self.assertEqual(coletar_viva_real(viva), 1)
        self.assertEqual(coletar_olx(olx), 1)

        self.assertEqual(Anuncio.objects.count(), 3)
        self.assertEqual(
            set(
                Anuncio.objects.values_list(
                    "fonte",
                    "identificador_externo",
                    "url",
                )
            ),
            {
                ("zap", "compartilhado-1", URL_COMPARTILHADA),
                ("viva-real", "compartilhado-1", URL_COMPARTILHADA),
                ("olx", "compartilhado-1", URL_COMPARTILHADA),
            },
        )

    def test_nao_gasta_cota_nem_escreve_visto(self):
        conta = Conta.objects.create_user(
            email="ana-olx@exemplo.com",
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

        self.assertEqual(coletar_olx(), 1)

        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 2)
        self.assertEqual(conta.pesquisas_mes_usadas, 3)
        self.assertEqual(conta.plano, Conta.PLANO_PADRAO)
        self.assertEqual(conta.creditos.get().restante, 4)
        nomes = {modelo.__name__ for modelo in apps.get_models()}
        self.assertNotIn("RadarVisto", nomes)
        tarefa = inspect.getsource(coletar_olx)
        self.assertNotIn("aceitar_pesquisa", tarefa)
        self.assertNotIn("cota", tarefa)
        self.assertNotIn("RadarVisto", tarefa)
        self.assertNotIn("coletar_zap", tarefa)
        self.assertNotIn("coletar_viva_real", tarefa)
        self.assertNotIn("coletar_olx", inspect.getsource(coletar_zap))
        self.assertNotIn("coletar_olx", inspect.getsource(coletar_viva_real))

    def test_sem_redis_e_sem_rede(self):
        def recusar(*args, **kwargs):
            raise AssertionError("a coleta abriu um socket")

        with (
            patch.object(socket, "socket", side_effect=recusar),
            patch.object(socket, "create_connection", side_effect=recusar),
        ):
            self.assertEqual(coletar_olx(), 1)
        self.assertEqual(Anuncio.objects.get().fonte, "olx")
        codigo = "\n".join(
            (
                (ROOT / "coleta" / "parser.py").read_text(encoding="utf-8"),
                (ROOT / "coleta" / "tasks.py").read_text(encoding="utf-8"),
            )
        )
        for termo in ("urlopen", "import requests", "import httpx", "import socket"):
            self.assertNotIn(termo, codigo)

    def test_fila_olx(self):
        from config.celery import app

        self.assertEqual(settings.CELERY_BROKER_URL, "redis://localhost:6379/0")
        self.assertEqual(
            settings.CELERY_TASK_ROUTES["coleta.tasks.coletar_olx"],
            {"queue": "olx"},
        )
        self.assertEqual(
            settings.CELERY_TASK_ROUTES["coleta.tasks.coletar_zap"],
            {"queue": "zap"},
        )
        self.assertEqual(
            settings.CELERY_TASK_ROUTES["coleta.tasks.coletar_viva_real"],
            {"queue": "viva-real"},
        )
        app.loader.import_default_modules()
        tarefa = app.tasks["coleta.tasks.coletar_olx"]
        self.assertEqual(tarefa.queue, "olx")
        self.assertEqual(tarefa.name, "coleta.tasks.coletar_olx")
