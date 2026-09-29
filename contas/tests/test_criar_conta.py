import uuid

from django.test import Client, TestCase
from django.urls import reverse

from contas.models import Conta

CORRETOR = {
    "tipo": "corretor",
    "nome": "Ana Lima",
    "email": "ana@exemplo.com",
    "telefone": "11987654321",
    "senha": "senha-segura",
    "creci": "123456-SP",
}

IMOBILIARIA = {
    "tipo": "imobiliaria",
    "razao_social": "Casa ABCD Ltda",
    "cnpj": "11.222.333/0001-81",
    "responsavel": "Bruno",
    "email": "casa@exemplo.com",
    "telefone": "1133334444",
    "senha": "senha-segura",
}

MENSAGEM_CRECI = "Informe o CRECI no formato número e UF."
MENSAGEM_CNPJ = "Informe um CNPJ com 14 dígitos e dígitos verificadores válidos."
STYLESHEET = "/static/contas/portal.css"


class CriarContaTests(TestCase):
    def test_corretor_signup_opens_the_client_area(self):
        response = self.client.post("/criar-conta/", CORRETOR)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/area/")
        self.assertEqual(reverse("area"), "/area/")
        self.assertIn("sessionid", response.cookies)
        self.assertEqual(Conta.objects.count(), 1)

        conta = Conta.objects.get()
        self.assertIsInstance(conta.pk, uuid.UUID)
        self.assertEqual(conta.tipo, Conta.TIPO_CORRETOR)
        self.assertEqual(conta.nome, "Ana Lima")
        self.assertEqual(conta.email, "ana@exemplo.com")
        self.assertEqual(conta.telefone, "11987654321")
        self.assertEqual(conta.creci, "123456-SP")
        self.assertEqual(conta.razao_social, "")
        self.assertEqual(conta.cnpj, "")
        self.assertEqual(conta.responsavel, "")
        self.assertNotEqual(conta.password, "senha-segura")
        self.assertNotIn("senha-segura", conta.password)
        self.assertTrue(conta.check_password("senha-segura"))

        area = self.client.get("/area/")
        self.assertEqual(area.status_code, 200)
        self.assertTemplateUsed(area, "contas/area.html")
        self.assertContains(area, "<h1>Área do cliente</h1>", html=True)
        self.assertContains(area, "Ana Lima")
        self.assertContains(area, STYLESHEET)
        self.assertEqual(area.wsgi_request.user.pk, conta.pk)

    def test_imobiliaria_signup_uses_the_same_area(self):
        response = self.client.post("/criar-conta/", IMOBILIARIA)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/area/")
        self.assertIn("sessionid", response.cookies)
        self.assertEqual(Conta.objects.count(), 1)

        conta = Conta.objects.get()
        self.assertEqual(conta.tipo, Conta.TIPO_IMOBILIARIA)
        self.assertEqual(conta.razao_social, "Casa ABCD Ltda")
        self.assertEqual(conta.cnpj, "11222333000181")
        self.assertEqual(conta.responsavel, "Bruno")
        self.assertEqual(conta.email, "casa@exemplo.com")
        self.assertEqual(conta.telefone, "1133334444")
        self.assertEqual(conta.nome, "")
        self.assertEqual(conta.creci, "")
        self.assertTrue(conta.check_password("senha-segura"))

        area = self.client.get("/area/")
        self.assertEqual(area.status_code, 200)
        self.assertTemplateUsed(area, "contas/area.html")
        self.assertContains(area, "<h1>Área do cliente</h1>", html=True)
        self.assertContains(area, "Casa ABCD Ltda")
        self.assertEqual(area.wsgi_request.user.pk, conta.pk)

    def test_creci_without_uf_does_not_create_a_row(self):
        for creci in ("123456", "SP", "123456-XX"):
            with self.subTest(creci=creci):
                response = self.client.post(
                    "/criar-conta/",
                    {**CORRETOR, "creci": creci},
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, MENSAGEM_CRECI)
                self.assertIn(MENSAGEM_CRECI, response.context["form"].errors["creci"])
                self.assertTemplateUsed(response, "contas/criar_conta.html")
                self.assertEqual(Conta.objects.count(), 0)
                self.assertNotIn("sessionid", response.cookies)

    def test_invalid_cnpj_does_not_create_a_row(self):
        for cnpj in ("11222333000182", "00000000000000"):
            with self.subTest(cnpj=cnpj):
                response = self.client.post(
                    "/criar-conta/",
                    {**IMOBILIARIA, "cnpj": cnpj},
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, MENSAGEM_CNPJ)
                self.assertIn(MENSAGEM_CNPJ, response.context["form"].errors["cnpj"])
                self.assertTemplateUsed(response, "contas/criar_conta.html")
                self.assertEqual(Conta.objects.count(), 0)
                self.assertNotIn("sessionid", response.cookies)

    def test_missing_type_does_not_create_a_row(self):
        dados = {chave: valor for chave, valor in CORRETOR.items() if chave != "tipo"}
        response = self.client.post("/criar-conta/", dados)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Escolha corretor ou imobiliária.")
        self.assertIn(
            "Escolha corretor ou imobiliária.",
            response.context["form"].errors["tipo"],
        )
        self.assertEqual(Conta.objects.count(), 0)
        self.assertNotIn("sessionid", response.cookies)

    def test_email_already_used_does_not_create_a_second_row(self):
        self.client.post("/criar-conta/", CORRETOR)
        self.assertEqual(Conta.objects.get().email, "ana@exemplo.com")

        response = Client().post(
            "/criar-conta/",
            {**CORRETOR, "email": "Ana@exemplo.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este e-mail já está em uso.")
        self.assertIn(
            "Este e-mail já está em uso.",
            response.context["form"].errors["email"],
        )
        self.assertEqual(Conta.objects.count(), 1)
        self.assertNotIn("sessionid", response.cookies)

    def test_email_is_stored_lowercase(self):
        response = self.client.post(
            "/criar-conta/",
            {**CORRETOR, "email": "Ana.Lima@Exemplo.com"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Conta.objects.get().email, "ana.lima@exemplo.com")

    def test_portal_links_to_signup_and_keeps_the_client_area_link(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<a href="/criar-conta/">Criar conta</a>',
            html=True,
        )
        self.assertContains(
            response,
            '<a href="/entrar/">Área do cliente</a>',
            html=True,
        )
        self.assertEqual(reverse("criar_conta"), "/criar-conta/")
        self.assertEqual(reverse("entrar"), "/entrar/")
        self.assertNotIn("sessionid", response.cookies)

    def test_anonymous_area_redirects_without_a_session(self):
        response = self.client.get("/area/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/entrar/")
        self.assertNotIn("sessionid", response.cookies)
        self.assertEqual(Conta.objects.count(), 0)
        self.assertNotContains(response, "Ana Lima", status_code=302)
        self.assertNotContains(response, "Casa ABCD Ltda", status_code=302)

    def test_accepted_creci_formats(self):
        amostras = {
            "123456-SP": "123456-SP",
            "123456/SP": "123456-SP",
            "123456SP": "123456-SP",
            "123456 SP": "123456-SP",
            "123456FSP": "123456-F-SP",
            "123456-F/SP": "123456-F-SP",
            "123456-f/sp": "123456-F-SP",
        }
        for indice, (creci, gravado) in enumerate(amostras.items()):
            with self.subTest(creci=creci):
                response = Client().post(
                    "/criar-conta/",
                    {**CORRETOR, "email": f"creci{indice}@exemplo.com", "creci": creci},
                )
                self.assertEqual(response.status_code, 302)
                conta = Conta.objects.get(email=f"creci{indice}@exemplo.com")
                self.assertEqual(conta.creci, gravado)

    def test_accepted_cnpj_without_punctuation(self):
        response = self.client.post(
            "/criar-conta/",
            {**IMOBILIARIA, "cnpj": "11222333000181"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Conta.objects.get().cnpj, "11222333000181")

    def test_blank_type_specific_fields_do_not_create_a_row(self):
        casos = [
            {**CORRETOR, "nome": "   ", "email": "vazio1@exemplo.com"},
            {**CORRETOR, "telefone": "   ", "email": "vazio2@exemplo.com"},
            {**IMOBILIARIA, "razao_social": "   ", "email": "vazio3@exemplo.com"},
            {**IMOBILIARIA, "responsavel": "   ", "email": "vazio4@exemplo.com"},
            {**IMOBILIARIA, "telefone": "   ", "email": "vazio5@exemplo.com"},
        ]
        for dados in casos:
            with self.subTest(email=dados["email"]):
                response = Client().post("/criar-conta/", dados)
                self.assertEqual(response.status_code, 200)
                self.assertFalse(Conta.objects.filter(email=dados["email"]).exists())

    def test_short_password_does_not_create_a_row(self):
        response = self.client.post(
            "/criar-conta/",
            {**CORRETOR, "senha": "curta-1", "email": "curta@exemplo.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Conta.objects.count(), 0)
        self.assertContains(response, "8")

    def test_other_type_columns_stay_blank(self):
        corretor = {
            **CORRETOR,
            "email": "fisica@exemplo.com",
            "razao_social": "Nao Salvar",
            "cnpj": "11.222.333/0001-81",
            "responsavel": "Ninguem",
        }
        imobiliaria = {
            **IMOBILIARIA,
            "email": "juridica@exemplo.com",
            "nome": "Nao Salvar",
            "creci": "123456-SP",
        }

        self.assertEqual(Client().post("/criar-conta/", corretor).status_code, 302)
        self.assertEqual(Client().post("/criar-conta/", imobiliaria).status_code, 302)

        fisica = Conta.objects.get(email="fisica@exemplo.com")
        self.assertEqual(fisica.razao_social, "")
        self.assertEqual(fisica.cnpj, "")
        self.assertEqual(fisica.responsavel, "")
        juridica = Conta.objects.get(email="juridica@exemplo.com")
        self.assertEqual(juridica.nome, "")
        self.assertEqual(juridica.creci, "")

    def test_conta_migration_is_the_first_app_migration(self):
        from importlib import import_module

        migration_module = import_module("contas.migrations.0001_initial")

        self.assertTrue(migration_module.Migration.initial)
        self.assertEqual(migration_module.Migration.dependencies, [])
