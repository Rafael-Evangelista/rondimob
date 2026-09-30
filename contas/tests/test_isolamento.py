import importlib.util
import uuid
from contextlib import contextmanager
from decimal import Decimal

import psycopg
from django.conf import settings
from django.db import connection, transaction
from django.test import Client, SimpleTestCase, TestCase, TransactionTestCase

from contas.cota import aceitar_pesquisa
from contas.isolamento import definir_conta, definir_email_de_login
from contas.models import Conta

SENHA = "senha-segura"
PAPEIS = {
    "rondimob_web": "dev-only-web",
    "rondimob_worker": "dev-only-worker",
}


def _pular_sem_postgres(teste):
    if connection.vendor != "postgresql":
        teste.skipTest("Isolation tests require PostgreSQL.")


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


def _conectar_dono():
    banco = connection.settings_dict
    kwargs = {"dbname": banco["NAME"], "autocommit": True}
    if banco.get("USER"):
        kwargs["user"] = banco["USER"]
    if banco.get("PASSWORD"):
        kwargs["password"] = banco["PASSWORD"]
    if banco.get("HOST"):
        kwargs["host"] = banco["HOST"]
    if banco.get("PORT"):
        kwargs["port"] = banco["PORT"]
    return psycopg.connect(**kwargs)


def _apagar(ids):
    if not ids:
        return
    with _conectar_dono() as conn:
        for conta_id in ids:
            conn.execute(
                "DELETE FROM contas_credito WHERE conta_id = %s",
                (conta_id,),
            )
            conn.execute("DELETE FROM contas_conta WHERE id = %s", (conta_id,))


def _inserir_credito(conn, conta_id, restante):
    credito_id = uuid.uuid4()
    with conn.transaction():
        conn.execute(
            "SELECT set_config('app.conta_id', %s, true)",
            (str(conta_id),),
        )
        conn.execute(
            """
            INSERT INTO contas_credito (id, preco, restante, criado_em, conta_id)
            VALUES (%s, 47.00, %s, now(), %s)
            """,
            (credito_id, restante, conta_id),
        )
    return credito_id


def _inserir(conn, nome, email):
    conta_id = uuid.uuid4()
    with conn.transaction():
        conn.execute("SELECT set_config('app.conta_id', %s, true)", (str(conta_id),))
        conn.execute(
            """
            INSERT INTO contas_conta (
                password, id, email, tipo, nome, telefone,
                creci, razao_social, cnpj, responsavel
            ) VALUES ('!', %s, %s, 'corretor', %s, '', '', '', '', '')
            """,
            (conta_id, email, nome),
        )
    return conta_id


@contextmanager
def _capturar_sql():
    captured = []

    def wrapper(execute, sql, params, many, context):
        captured.append((sql, list(params) if params is not None else None))
        return execute(sql, params, many, context)

    with connection.execute_wrapper(wrapper):
        yield captured


def _indice(captured, predicado):
    for indice, (sql, params) in enumerate(captured):
        if predicado(sql, params):
            return indice
    raise AssertionError(captured)


def _set_config(chave, valor=None):
    def predicado(sql, params):
        if "set_config" not in sql or ", true)" not in sql:
            return False
        if not params or params[0] != chave:
            return False
        if valor is None:
            return True
        return str(params[1]) == str(valor)

    return predicado


def _tabela_conta(sql, _params):
    return "contas_conta" in sql


def _insert_conta(sql, _params):
    return "INSERT" in sql.upper() and "contas_conta" in sql


class IsolamentoConfigTests(SimpleTestCase):
    def test_middleware_is_between_session_and_auth(self):
        from config import settings as production_settings

        middle = production_settings.MIDDLEWARE
        session = middle.index("django.contrib.sessions.middleware.SessionMiddleware")
        auth = middle.index("django.contrib.auth.middleware.AuthenticationMiddleware")
        isolamento = middle.index("contas.middleware.IsolamentoDaContaMiddleware")
        self.assertLess(session, isolamento)
        self.assertLess(isolamento, auth)
        self.assertNotIn("django_tenants", production_settings.INSTALLED_APPS)


class HelperTests(TestCase):
    def test_helper_calls_set_config_only_on_postgresql(self):
        with transaction.atomic():
            with _capturar_sql() as captured:
                definir_conta("conta-1")
                definir_email_de_login("ana@exemplo.com")
        configuracoes = [
            (sql, params)
            for sql, params in captured
            if "set_config" in sql
        ]
        if connection.vendor == "postgresql":
            self.assertEqual(
                configuracoes,
                [
                    ("SELECT set_config(%s, %s, true)", ["app.conta_id", "conta-1"]),
                    (
                        "SELECT set_config(%s, %s, true)",
                        ["app.login_email", "ana@exemplo.com"],
                    ),
                ],
            )
        else:
            self.assertEqual(configuracoes, [])


class IsolamentoPolicyTests(TestCase):
    def test_role_reads_and_updates_only_its_row(self):
        _pular_sem_postgres(self)
        for papel in PAPEIS:
            with self.subTest(papel=papel):
                self._ler_e_atualizar(papel)

    def _ler_e_atualizar(self, papel):
        ids = []
        conn = _conectar_papel(papel)
        try:
            conta_a = _inserir(conn, "Ana", f"a-{papel}@exemplo.com")
            conta_b = _inserir(conn, "Bruno", f"b-{papel}@exemplo.com")
            ids.extend((conta_a, conta_b))
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_a),),
                )
                linhas = conn.execute(
                    "SELECT id::text, nome FROM contas_conta ORDER BY nome"
                ).fetchall()
                self.assertEqual(linhas, [(str(conta_a), "Ana")])
                conn.execute(
                    "UPDATE contas_conta SET nome = %s WHERE id = %s",
                    ("Ana Nova", conta_a),
                )
                alteradas = conn.execute(
                    "UPDATE contas_conta SET nome = %s WHERE id = %s",
                    ("Bruno Hack", conta_b),
                ).rowcount
                self.assertEqual(alteradas, 0)
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_a),),
                )
                self.assertEqual(
                    conn.execute("SELECT nome FROM contas_conta").fetchall(),
                    [("Ana Nova",)],
                )
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_b),),
                )
                self.assertEqual(
                    conn.execute("SELECT nome FROM contas_conta").fetchall(),
                    [("Bruno",)],
                )
        finally:
            conn.close()
            _apagar(ids)

    def test_web_role_sees_only_its_free_search_counter(self):
        _pular_sem_postgres(self)
        ids = []
        conn = _conectar_papel("rondimob_web")
        try:
            conta_a = _inserir(conn, "Ana", "cota-a@exemplo.com")
            conta_b = _inserir(conn, "Bruno", "cota-b@exemplo.com")
            ids.extend((conta_a, conta_b))
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_a),),
                )
                self.assertEqual(
                    conn.execute(
                        """
                        SELECT pesquisas_gratis_usadas, criada_em IS NOT NULL
                        FROM contas_conta
                        """
                    ).fetchall(),
                    [(0, True)],
                )
                conn.execute("UPDATE contas_conta SET pesquisas_gratis_usadas = 3")
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_b),),
                )
                conn.execute("UPDATE contas_conta SET pesquisas_gratis_usadas = 7")
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_a),),
                )
                self.assertEqual(
                    conn.execute(
                        "SELECT pesquisas_gratis_usadas FROM contas_conta"
                    ).fetchall(),
                    [(3,)],
                )
                alteradas = conn.execute(
                    """
                    UPDATE contas_conta
                    SET pesquisas_gratis_usadas = 9
                    WHERE id = %s
                    """,
                    (conta_b,),
                ).rowcount
                self.assertEqual(alteradas, 0)
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_b),),
                )
                self.assertEqual(
                    conn.execute(
                        "SELECT pesquisas_gratis_usadas FROM contas_conta"
                    ).fetchall(),
                    [(7,)],
                )
        finally:
            conn.close()
            _apagar(ids)

    def test_web_role_sees_only_its_plan(self):
        _pular_sem_postgres(self)
        ids = []
        conn = _conectar_papel("rondimob_web")
        try:
            conta_a = _inserir(conn, "Ana", "plano-a@exemplo.com")
            conta_b = _inserir(conn, "Bruno", "plano-b@exemplo.com")
            ids.extend((conta_a, conta_b))
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_a),),
                )
                self.assertEqual(
                    conn.execute(
                        """
                        SELECT plano, pesquisas_mes_usadas, mes_da_cota
                        FROM contas_conta
                        """
                    ).fetchall(),
                    [("", 0, None)],
                )
                conn.execute(
                    """
                    UPDATE contas_conta
                    SET plano = 'padrao', pesquisas_mes_usadas = 4
                    """
                )
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_b),),
                )
                conn.execute(
                    """
                    UPDATE contas_conta
                    SET plano = 'plus', pesquisas_mes_usadas = 9
                    """
                )
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_a),),
                )
                self.assertEqual(
                    conn.execute(
                        "SELECT plano, pesquisas_mes_usadas FROM contas_conta"
                    ).fetchall(),
                    [("padrao", 4)],
                )
                alteradas = conn.execute(
                    """
                    UPDATE contas_conta
                    SET plano = 'plus', pesquisas_mes_usadas = 1
                    WHERE id = %s
                    """,
                    (conta_b,),
                ).rowcount
                self.assertEqual(alteradas, 0)
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_b),),
                )
                self.assertEqual(
                    conn.execute(
                        "SELECT plano, pesquisas_mes_usadas FROM contas_conta"
                    ).fetchall(),
                    [("plus", 9)],
                )
        finally:
            conn.close()
            _apagar(ids)

    def test_aceitar_pesquisa_sets_conta_id_before_the_locked_read(self):
        _pular_sem_postgres(self)
        conta = Conta.objects.create_user(
            email="cota-lock@exemplo.com",
            password=SENHA,
            tipo=Conta.TIPO_CORRETOR,
            nome="Ana Lima",
        )
        with _capturar_sql() as captured:
            self.assertTrue(aceitar_pesquisa(conta))
        leitura = _indice(
            captured,
            lambda sql, _params: "FOR UPDATE" in sql.upper() and "contas_conta" in sql,
        )
        self.assertLess(
            _indice(captured, _set_config("app.conta_id", conta.pk)),
            leitura,
        )
        escrita = _indice(
            captured,
            lambda sql, _params: sql.lstrip().upper().startswith("UPDATE")
            and "pesquisas_gratis_usadas" in sql,
        )
        self.assertLess(leitura, escrita)
        conta.refresh_from_db()
        self.assertEqual(conta.pesquisas_gratis_usadas, 1)

    def test_setting_dies_with_the_transaction(self):
        _pular_sem_postgres(self)
        for papel in PAPEIS:
            with self.subTest(papel=papel):
                self._configuracao_morre(papel)

    def _configuracao_morre(self, papel):
        ids = []
        conn = _conectar_papel(papel)
        try:
            conta_a = _inserir(conn, "Ana", f"morre-a-{papel}@exemplo.com")
            conta_b = _inserir(conn, "Bruno", f"morre-b-{papel}@exemplo.com")
            ids.extend((conta_a, conta_b))
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_a),),
                )
                self.assertEqual(
                    conn.execute("SELECT id::text FROM contas_conta").fetchall(),
                    [(str(conta_a),)],
                )
            with conn.transaction():
                atual = conn.execute(
                    "SELECT current_setting('app.conta_id', true)"
                ).fetchone()[0]
                self.assertIn(atual, (None, ""))
                self.assertEqual(
                    conn.execute("SELECT id FROM contas_conta").fetchall(),
                    [],
                )
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_b),),
                )
                self.assertEqual(
                    conn.execute("SELECT id::text FROM contas_conta").fetchall(),
                    [(str(conta_b),)],
                )
        finally:
            conn.close()
            _apagar(ids)

    def test_with_check_rejects_an_insert_for_another_id(self):
        _pular_sem_postgres(self)
        ids = []
        conn = _conectar_papel("rondimob_web")
        try:
            conta_a = _inserir(conn, "Ana", "check-a@exemplo.com")
            ids.append(conta_a)
            outro = uuid.uuid4()
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with conn.transaction():
                    conn.execute(
                        "SELECT set_config('app.conta_id', %s, true)",
                        (str(conta_a),),
                    )
                    conn.execute(
                        """
                        INSERT INTO contas_conta (
                            password, id, email, tipo, nome, telefone,
                            creci, razao_social, cnpj, responsavel
                        ) VALUES (
                            '!', %s, 'check-outra@exemplo.com', 'corretor',
                            'Outra', '', '', '', '', ''
                        )
                        """,
                        (outro,),
                    )
        finally:
            conn.close()
            _apagar(ids)

    def test_login_email_returns_only_that_account(self):
        _pular_sem_postgres(self)
        ids = []
        conn = _conectar_papel("rondimob_web")
        try:
            email_a = "login-a@exemplo.com"
            conta_a = _inserir(conn, "Ana", email_a)
            conta_b = _inserir(conn, "Bruno", "login-b@exemplo.com")
            ids.extend((conta_a, conta_b))
            with conn.transaction():
                conn.execute("SELECT set_config('app.conta_id', '', true)")
                conn.execute(
                    "SELECT set_config('app.login_email', %s, true)",
                    (email_a,),
                )
                self.assertEqual(
                    conn.execute("SELECT email FROM contas_conta").fetchall(),
                    [(email_a,)],
                )
        finally:
            conn.close()
            _apagar(ids)

    def test_roles_policy_and_single_private_table(self):
        _pular_sem_postgres(self)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.relname
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relrowsecurity
                ORDER BY 1
                """
            )
            self.assertEqual(
                [linha[0] for linha in cursor.fetchall()],
                ["contas_conta", "contas_credito"],
            )
            cursor.execute(
                """
                SELECT c.relrowsecurity, c.relforcerowsecurity
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'contas_conta'
                """
            )
            self.assertEqual(cursor.fetchone(), (True, True))
            cursor.execute(
                """
                SELECT pol.polname,
                       pg_get_expr(pol.polqual, pol.polrelid),
                       pg_get_expr(pol.polwithcheck, pol.polrelid)
                FROM pg_policy pol
                JOIN pg_class c ON c.oid = pol.polrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'contas_conta'
                """
            )
            politicas = cursor.fetchall()
        self.assertEqual(len(politicas), 1)
        nome, usando, checagem = politicas[0]
        self.assertEqual(nome, "conta_isola")
        self.assertIn("app.conta_id", usando)
        self.assertIn("app.login_email", usando)
        self.assertIn("app.conta_id", checagem)
        self.assertNotIn("app.login_email", checagem)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.relrowsecurity, c.relforcerowsecurity
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'contas_credito'
                """
            )
            self.assertEqual(cursor.fetchone(), (True, True))
            cursor.execute(
                """
                SELECT pol.polname,
                       pg_get_expr(pol.polqual, pol.polrelid),
                       pg_get_expr(pol.polwithcheck, pol.polrelid)
                FROM pg_policy pol
                JOIN pg_class c ON c.oid = pol.polrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'contas_credito'
                """
            )
            politicas_credito = cursor.fetchall()
        self.assertEqual(len(politicas_credito), 1)
        nome_credito, usando_credito, checagem_credito = politicas_credito[0]
        self.assertEqual(nome_credito, "conta_isola")
        self.assertIn("app.conta_id", usando_credito)
        self.assertNotIn("app.login_email", usando_credito)
        self.assertIn("app.conta_id", checagem_credito)
        self.assertNotIn("app.login_email", checagem_credito)
        self.assertIsNone(importlib.util.find_spec("django_tenants"))
        self.assertNotIn("django_tenants", settings.INSTALLED_APPS)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT privilege_type
                FROM information_schema.role_table_grants
                WHERE grantee = 'rondimob_web'
                  AND table_schema = 'public'
                  AND table_name = 'django_session'
                """
            )
            privilegios = {linha[0] for linha in cursor.fetchall()}
        self.assertTrue({"SELECT", "INSERT", "UPDATE", "DELETE"} <= privilegios)

        for papel in PAPEIS:
            with self.subTest(papel=papel):
                with _conectar_papel(papel) as conn:
                    papel_atual, superuser, bypass, dono = conn.execute(
                        """
                        SELECT current_user, rolsuper, rolbypassrls,
                               pg_get_userbyid(c.relowner)
                        FROM pg_roles
                        JOIN pg_class c ON true
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE rolname = current_user
                          AND n.nspname = 'public'
                          AND c.relname = 'contas_conta'
                        """
                    ).fetchone()
                    dono_credito = conn.execute(
                        """
                        SELECT pg_get_userbyid(c.relowner)
                        FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE n.nspname = 'public' AND c.relname = 'contas_credito'
                        """
                    ).fetchone()[0]
                    privilegios_credito = {
                        linha[0]
                        for linha in conn.execute(
                            """
                            SELECT privilege_type
                            FROM information_schema.role_table_grants
                            WHERE grantee = %s
                              AND table_schema = 'public'
                              AND table_name = 'contas_credito'
                            """,
                            (papel,),
                        ).fetchall()
                    }
                self.assertEqual(papel_atual, papel)
                self.assertFalse(superuser)
                self.assertFalse(bypass)
                self.assertNotEqual(dono, papel)
                self.assertNotEqual(dono_credito, papel)
                self.assertTrue(
                    {"SELECT", "INSERT", "UPDATE", "DELETE"} <= privilegios_credito
                )

    def test_web_role_sees_only_its_credit(self):
        _pular_sem_postgres(self)
        ids = []
        conn = _conectar_papel("rondimob_web")
        try:
            conta_a = _inserir(conn, "Ana", "credito-a@exemplo.com")
            conta_b = _inserir(conn, "Bruno", "credito-b@exemplo.com")
            ids.extend((conta_a, conta_b))
            _inserir_credito(conn, conta_a, 10)
            _inserir_credito(conn, conta_b, 4)
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_a),),
                )
                self.assertEqual(
                    conn.execute(
                        """
                        SELECT conta_id::text, restante, preco
                        FROM contas_credito
                        """
                    ).fetchall(),
                    [(str(conta_a), 10, Decimal("47.00"))],
                )
                alteradas = conn.execute(
                    """
                    UPDATE contas_credito
                    SET restante = 1
                    WHERE conta_id = %s
                    """,
                    (conta_b,),
                ).rowcount
                self.assertEqual(alteradas, 0)
                self.assertEqual(
                    conn.execute("SELECT restante FROM contas_credito").fetchall(),
                    [(10,)],
                )
            with conn.transaction():
                conn.execute(
                    "SELECT set_config('app.conta_id', %s, true)",
                    (str(conta_b),),
                )
                self.assertEqual(
                    conn.execute(
                        "SELECT conta_id::text, restante FROM contas_credito"
                    ).fetchall(),
                    [(str(conta_b), 4)],
                )
        finally:
            conn.close()
            _apagar(ids)

    def test_login_sets_login_email_before_the_query(self):
        _pular_sem_postgres(self)
        conta = Conta.objects.create_user(
            email="ana-login@exemplo.com",
            password=SENHA,
            tipo=Conta.TIPO_CORRETOR,
            nome="Ana Lima",
        )
        with _capturar_sql() as captured:
            resposta = Client().post(
                "/entrar/",
                {"email": "Ana-Login@exemplo.com", "senha": SENHA},
            )
        self.assertEqual(resposta.status_code, 302)
        self.assertLess(
            _indice(captured, _set_config("app.login_email", conta.email)),
            _indice(captured, _tabela_conta),
        )

    def test_area_sets_conta_id_before_the_query(self):
        _pular_sem_postgres(self)
        conta = Conta.objects.create_user(
            email="ana-area@exemplo.com",
            password=SENHA,
            tipo=Conta.TIPO_CORRETOR,
            nome="Ana Lima",
        )
        cliente = Client()
        self.assertEqual(
            cliente.post(
                "/entrar/",
                {"email": conta.email, "senha": SENHA},
            ).status_code,
            302,
        )
        with _capturar_sql() as captured:
            resposta = cliente.get("/area/")
        self.assertEqual(resposta.status_code, 200)
        self.assertLess(
            _indice(captured, _set_config("app.conta_id", conta.pk)),
            _indice(captured, _tabela_conta),
        )

    def test_signup_sets_conta_id_before_insert(self):
        _pular_sem_postgres(self)
        dados = {
            "tipo": "corretor",
            "nome": "Ana Lima",
            "email": "ana-nova@exemplo.com",
            "telefone": "11987654321",
            "senha": SENHA,
            "creci": "123456-SP",
        }
        with _capturar_sql() as captured:
            resposta = Client().post("/criar-conta/", dados)
        self.assertEqual(resposta.status_code, 302)
        conta = Conta.objects.get(email="ana-nova@exemplo.com")
        self.assertLess(
            _indice(captured, _set_config("app.conta_id", conta.pk)),
            _indice(captured, _insert_conta),
        )
        self.assertLess(
            _indice(captured, _set_config("app.login_email", conta.email)),
            _indice(captured, _tabela_conta),
        )

    def test_reset_and_task_set_conta_id_before_the_load(self):
        _pular_sem_postgres(self)
        from contas.tasks import preparar_link_de_recuperacao

        conta = Conta.objects.create_user(
            email="ana-reset@exemplo.com",
            password=SENHA,
            tipo=Conta.TIPO_CORRETOR,
            nome="Ana Lima",
        )
        with _capturar_sql() as captured:
            link = preparar_link_de_recuperacao(str(conta.pk))
        self.assertLess(
            _indice(captured, _set_config("app.conta_id", conta.pk)),
            _indice(captured, _tabela_conta),
        )
        with _capturar_sql() as captured:
            resposta = Client().get(link)
        self.assertEqual(resposta.status_code, 200)
        self.assertLess(
            _indice(captured, _set_config("app.conta_id", conta.pk)),
            _indice(captured, _tabela_conta),
        )

    def test_recovery_lookup_sets_login_email_before_the_query(self):
        _pular_sem_postgres(self)
        from unittest.mock import patch

        conta = Conta.objects.create_user(
            email="ana-recupera@exemplo.com",
            password=SENHA,
            tipo=Conta.TIPO_CORRETOR,
            nome="Ana Lima",
        )
        with patch("contas.views.preparar_link_de_recuperacao.delay") as delay:
            with _capturar_sql() as captured:
                resposta = Client().post(
                    "/recuperar-senha/",
                    {"email": "Ana-Recupera@exemplo.com"},
                )
        self.assertEqual(resposta.status_code, 200)
        delay.assert_called_once_with(str(conta.pk))
        self.assertLess(
            _indice(captured, _set_config("app.login_email", conta.email)),
            _indice(captured, _tabela_conta),
        )


class IsolamentoPolicyGrantTests(TestCase):
    def test_web_role_can_select_django_migrations(self):
        _pular_sem_postgres(self)
        with _conectar_papel("rondimob_web") as conn:
            linhas = conn.execute(
                """
                SELECT app, name
                FROM public.django_migrations
                WHERE app = 'contas' AND name = '0002_isolamento_da_conta'
                """
            ).fetchall()
        self.assertEqual(linhas, [("contas", "0002_isolamento_da_conta")])


class IsolamentoTransacaoTests(TransactionTestCase):
    def test_area_keeps_conta_id_only_inside_the_request_transaction(self):
        _pular_sem_postgres(self)
        conta = Conta.objects.create_user(
            email="ana-transacao@exemplo.com",
            password=SENHA,
            tipo=Conta.TIPO_CORRETOR,
            nome="Ana Lima",
        )
        cliente = Client()
        self.assertEqual(
            cliente.post("/entrar/", {"email": conta.email, "senha": SENHA}).status_code,
            302,
        )
        vistos = []

        def wrapper(execute, sql, params, many, context):
            if "contas_conta" in sql:
                execute(
                    "SELECT current_setting('app.conta_id', true)",
                    None,
                    False,
                    context,
                )
                vistos.append(context["cursor"].fetchone()[0])
            return execute(sql, params, many, context)

        with connection.execute_wrapper(wrapper):
            resposta = cliente.get("/area/")
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(vistos)
        self.assertTrue(all(valor == str(conta.pk) for valor in vistos))

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_setting('app.conta_id', true)")
                seguinte = cursor.fetchone()[0]
        self.assertIn(seguinte, (None, ""))
