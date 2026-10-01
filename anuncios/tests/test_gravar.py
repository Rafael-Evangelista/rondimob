import importlib
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import psycopg
from django.db import IntegrityError, connection, models, transaction
from django.test import TestCase

from anuncios.gravar import gravar
from anuncios.models import Anuncio, Preco

PAPEIS = {
    "rondimob_web": "dev-only-web",
    "rondimob_worker": "dev-only-worker",
}
TABELAS = ("anuncios_anuncio", "anuncios_preco", "coleta_falha")


def _dados(**kwargs):
    dados = {
        "fonte": "zap",
        "identificador_externo": "ext-1",
        "url": "https://exemplo.invalid/a",
        "titulo": "Apartamento",
        "endereco": "Rua Exemplo",
        "descricao": "Descrição",
        "preco": Decimal("650000.00"),
        "area": Decimal("60"),
        "quartos": 2,
        "banheiros": 1,
        "vagas": 1,
        "cidade": "santo andré",
        "bairro": "centro",
        "tipo": "apartamento",
        "imobiliaria": "alfa",
    }
    dados.update(kwargs)
    return dados


def _pular_sem_postgres(teste):
    if connection.vendor != "postgresql":
        teste.skipTest("Worker grant requires PostgreSQL.")


def _conectar_papel(papel):
    banco = connection.settings_dict
    conn = psycopg.connect(
        dbname=banco["NAME"],
        user=papel,
        password=PAPEIS[papel],
        host="127.0.0.1",
        port=banco["PORT"] or 5432,
        autocommit=True,
    )
    conn.execute("SET lock_timeout = '5s'")
    return conn


class GravarTests(TestCase):
    def test_tipos_e_dependencia_da_migracao(self):
        migration_module = importlib.import_module("anuncios.migrations.0001_initial")

        for nome in ("preco", "area"):
            self.assertIsInstance(Anuncio._meta.get_field(nome), models.DecimalField)
        for nome in ("quartos", "banheiros", "vagas"):
            self.assertIsInstance(Anuncio._meta.get_field(nome), models.IntegerField)
        self.assertIsInstance(Preco._meta.get_field("valor"), models.DecimalField)
        self.assertNotIn("conta", {campo.name for campo in Anuncio._meta.fields})
        dependencies = migration_module.Migration.dependencies
        self.assertIn(("contas", "0002_isolamento_da_conta"), dependencies)

    def test_mesmo_preco_atualiza_so_o_instante(self):
        primeiro = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
        segundo = datetime(2026, 9, 30, 13, 0, tzinfo=timezone.utc)
        instantes = [primeiro, segundo]

        def agora(tz=None):
            return instantes.pop(0)

        with patch("anuncios.gravar.datetime") as relogio:
            relogio.now.side_effect = agora
            gravar(_dados(preco=Decimal("650000.00")))
            gravar(_dados(preco=Decimal("650000"), cidade="diadema"))

        anuncio = Anuncio.objects.get()
        self.assertEqual(anuncio.coletado_em, segundo)
        self.assertEqual(anuncio.cidade, "santo andré")
        self.assertEqual(Preco.objects.count(), 1)
        self.assertEqual(Preco.objects.get().coletado_em, primeiro)
        self.assertEqual(anuncio.coletado_em.utcoffset(), timedelta(0))

    def test_preco_novo_abre_outra_linha(self):
        gravar(_dados())
        gravar(_dados(preco=Decimal("700000.00"), cidade="diadema"))
        anuncio = Anuncio.objects.get()
        self.assertEqual(anuncio.preco, Decimal("700000.00"))
        self.assertEqual(anuncio.cidade, "diadema")
        self.assertEqual(Preco.objects.count(), 2)

    def test_sem_id_a_mesma_url_nao_cria_outro(self):
        gravar(_dados(identificador_externo=""))
        gravar(_dados(identificador_externo="", titulo="Outro"))
        self.assertEqual(Anuncio.objects.count(), 1)
        self.assertEqual(Anuncio.objects.get().titulo, "Apartamento")

    def test_dois_ids_vazios_com_urls_diferentes_criam_dois(self):
        gravar(_dados(identificador_externo="", url="https://exemplo.invalid/um"))
        gravar(_dados(identificador_externo="", url="https://exemplo.invalid/dois"))
        self.assertEqual(Anuncio.objects.count(), 2)

    def test_chave_recusa_duplicata(self):
        gravar(_dados())
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Anuncio.objects.create(
                    fonte="zap",
                    identificador_externo="ext-1",
                    url="https://exemplo.invalid/outra",
                    preco=Decimal("1.00"),
                    coletado_em=datetime(2026, 9, 30, tzinfo=timezone.utc),
                )
        gravar(_dados(identificador_externo="", url="https://exemplo.invalid/livre"))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Anuncio.objects.create(
                    fonte="zap",
                    identificador_externo="",
                    url="https://exemplo.invalid/livre",
                    preco=Decimal("1.00"),
                    coletado_em=datetime(2026, 9, 30, tzinfo=timezone.utc),
                )


class WorkerGrantTests(TestCase):
    def test_worker_insere_no_corpus_sem_rls(self):
        _pular_sem_postgres(self)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.relname
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = ANY(%s)
                  AND c.relrowsecurity
                """,
                (list(TABELAS),),
            )
            self.assertEqual(cursor.fetchall(), [])
            cursor.execute(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'anuncios_anuncio'
                  AND column_name = ANY(%s)
                ORDER BY column_name
                """,
                (
                    [
                        "area",
                        "banheiros",
                        "coletado_em",
                        "preco",
                        "quartos",
                        "vagas",
                    ],
                ),
            )
            self.assertEqual(
                cursor.fetchall(),
                [
                    ("anuncios_anuncio", "area", "numeric"),
                    ("anuncios_anuncio", "banheiros", "integer"),
                    ("anuncios_anuncio", "coletado_em", "timestamp with time zone"),
                    ("anuncios_anuncio", "preco", "numeric"),
                    ("anuncios_anuncio", "quartos", "integer"),
                    ("anuncios_anuncio", "vagas", "integer"),
                ],
            )
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'anuncios_anuncio'
                  AND column_name = 'conta_id'
                """
            )
            self.assertEqual(cursor.fetchall(), [])

        for papel in PAPEIS:
            with self.subTest(papel=papel):
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT table_name, privilege_type
                        FROM information_schema.role_table_grants
                        WHERE grantee = %s
                          AND table_schema = 'public'
                          AND table_name = ANY(%s)
                        """,
                        (papel, list(TABELAS)),
                    )
                    concedidos = {(linha[0], linha[1]) for linha in cursor.fetchall()}
                esperados = {
                    (tabela, privilegio)
                    for tabela in TABELAS
                    for privilegio in ("SELECT", "INSERT", "UPDATE", "DELETE")
                }
                self.assertTrue(esperados <= concedidos)

        anuncio_id = uuid.uuid4()
        preco_id = uuid.uuid4()
        falha_id = uuid.uuid4()
        conn = _conectar_papel("rondimob_worker")
        try:
            conn.execute(
                """
                INSERT INTO anuncios_anuncio (
                    id, fonte, identificador_externo, url, titulo, endereco,
                    descricao, preco, area, quartos, banheiros, vagas,
                    cidade, bairro, tipo, imobiliaria, coletado_em
                ) VALUES (
                    %s, 'zap', 'grant-1', 'https://exemplo.invalid/grant',
                    '', '', '', 650000, 60, 2, 1, 1,
                    'santo andré', 'centro', 'apartamento', 'alfa', now()
                )
                """,
                (anuncio_id,),
            )
            conn.execute(
                """
                INSERT INTO anuncios_preco (id, valor, coletado_em, anuncio_id)
                VALUES (%s, 650000, now(), %s)
                """,
                (preco_id, anuncio_id),
            )
            conn.execute(
                """
                INSERT INTO coleta_falha (id, fonte, mensagem, criada_em)
                VALUES (%s, 'zap', 'teste', now())
                """,
                (falha_id,),
            )
            self.assertEqual(
                conn.execute(
                    "SELECT preco FROM anuncios_anuncio WHERE id = %s",
                    (anuncio_id,),
                ).fetchone()[0],
                Decimal("650000"),
            )
        finally:
            conn.execute("DELETE FROM anuncios_preco WHERE id = %s", (preco_id,))
            conn.execute("DELETE FROM anuncios_anuncio WHERE id = %s", (anuncio_id,))
            conn.execute("DELETE FROM coleta_falha WHERE id = %s", (falha_id,))
            conn.close()
