import re
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from contas.models import Conta
from contas.tasks import preparar_link_de_recuperacao

SENHA = "senha-segura"
SENHA_NOVA = "nova-senha-8"
MENSAGEM_LOGIN = "E-mail ou senha incorretos."
MENSAGEM_RECUPERACAO = (
    "Se houver uma conta com esse e-mail, o pedido de nova senha foi registrado."
)
MENSAGEM_LINK = "Este link não vale mais."
STYLESHEET = "/static/contas/portal.css"


def _token_csrf(resposta):
    correspondencia = re.search(
        r'name="csrfmiddlewaretoken" value="([^"]+)"',
        resposta.content.decode(),
    )
    if correspondencia is None:
        raise AssertionError("csrfmiddlewaretoken ausente")
    return correspondencia.group(1)


def _formulario_volta_ao_caminho(resposta, caminho):
    tag = re.search(r"<form\b[^>]*>", resposta.content.decode(), flags=re.IGNORECASE)
    if tag is None:
        return False
    acao = re.search(r"""\baction=(['"])(.*?)\1""", tag.group(0))
    return acao is None or acao.group(2) == caminho


def criar_conta(**kwargs):
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


class SessaoTests(TestCase):
    def test_login_opens_the_account_and_the_session_survives(self):
        conta = criar_conta()
        outra = criar_conta(
            email="bruno@exemplo.com",
            nome="Bruno Dias",
            creci="654321-SP",
        )

        response = self.client.post(
            "/entrar/",
            {"email": "Ana@exemplo.com", "senha": SENHA},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/area/")
        self.assertEqual(reverse("entrar"), "/entrar/")
        self.assertEqual(reverse("area"), "/area/")
        self.assertIn("sessionid", response.cookies)

        primeira = self.client.get("/area/")
        segunda = self.client.get("/area/")
        self.assertEqual(primeira.status_code, 200)
        self.assertEqual(segunda.status_code, 200)
        self.assertContains(primeira, "<h1>Área do cliente</h1>", html=True)
        self.assertContains(primeira, "Ana Lima")
        self.assertNotContains(primeira, "Bruno Dias")
        self.assertContains(primeira, STYLESHEET)
        self.assertContains(primeira, 'action="/sair/"')
        self.assertEqual(primeira.wsgi_request.user.pk, conta.pk)
        self.assertEqual(segunda.wsgi_request.user.pk, conta.pk)
        self.assertNotEqual(segunda.wsgi_request.user.pk, outra.pk)

    def test_logout_closes_the_area_and_the_old_cookie_authenticates_nobody(self):
        conta = criar_conta()
        outra = criar_conta(
            email="bruno@exemplo.com",
            nome="Bruno Dias",
            creci="654321-SP",
        )
        self.client.post("/entrar/", {"email": conta.email, "senha": SENHA})
        cookie = self.client.cookies["sessionid"].value

        get_sair = self.client.get("/sair/")
        self.assertEqual(get_sair.status_code, 405)
        ainda = self.client.get("/area/")
        self.assertEqual(ainda.status_code, 200)
        self.assertEqual(ainda.wsgi_request.user.pk, conta.pk)

        response = self.client.post("/sair/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/entrar/")
        self.assertEqual(reverse("sair"), "/sair/")

        area = self.client.get("/area/")
        self.assertEqual(area.status_code, 302)
        self.assertEqual(area["Location"], "/entrar/")

        replay = Client()
        replay.cookies["sessionid"] = cookie
        reaberta = replay.get("/area/")
        self.assertEqual(reaberta.status_code, 302)
        self.assertEqual(reaberta["Location"], "/entrar/")
        self.assertFalse(reaberta.wsgi_request.user.is_authenticated)
        self.assertNotEqual(getattr(reaberta.wsgi_request.user, "pk", None), conta.pk)
        self.assertNotEqual(getattr(reaberta.wsgi_request.user, "pk", None), outra.pk)
        self.assertNotContains(reaberta, "Ana Lima", status_code=302)
        self.assertNotContains(reaberta, "Bruno Dias", status_code=302)

        bruno = Client()
        entrada = bruno.post("/entrar/", {"email": outra.email, "senha": SENHA})
        self.assertEqual(entrada.status_code, 302)
        self.assertEqual(entrada.wsgi_request.user.pk, outra.pk)
        de_novo = Client()
        de_novo.cookies["sessionid"] = cookie
        repetida = de_novo.get("/area/")
        self.assertEqual(repetida.status_code, 302)
        self.assertEqual(repetida["Location"], "/entrar/")
        self.assertFalse(repetida.wsgi_request.user.is_authenticated)

    def test_wrong_email_or_password_opens_nothing(self):
        conta = criar_conta()
        casos = (
            {"email": "nao-existe@exemplo.com", "senha": SENHA},
            {"email": conta.email, "senha": "senha-errada"},
        )
        for dados in casos:
            with self.subTest(email=dados["email"]):
                cliente = Client()
                response = cliente.post("/entrar/", dados)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, MENSAGEM_LOGIN)
                self.assertContains(response, 'name="email"')
                self.assertContains(response, 'name="senha"')
                self.assertTemplateUsed(response, "contas/entrar.html")
                self.assertNotIn("sessionid", response.cookies)
                self.assertFalse(response.wsgi_request.user.is_authenticated)
                area = cliente.get("/area/")
                self.assertEqual(area.status_code, 302)
                self.assertEqual(area["Location"], "/entrar/")

    def test_recovery_request_enqueues_without_a_token_or_a_new_password(self):
        conta = criar_conta()
        hash_antes = conta.password

        with patch("contas.views.preparar_link_de_recuperacao.delay") as delay:
            conhecida = self.client.post(
                "/recuperar-senha/",
                {"email": "Ana@exemplo.com"},
            )
            desconhecida = Client().post(
                "/recuperar-senha/",
                {"email": "ninguem@exemplo.com"},
            )

        self.assertEqual(conhecida.status_code, 200)
        self.assertEqual(desconhecida.status_code, 200)
        self.assertContains(conhecida, MENSAGEM_RECUPERACAO)
        self.assertEqual(conhecida.content, desconhecida.content)
        self.assertNotIn("token", conhecida.content.decode().lower())
        self.assertNotRegex(
            conhecida.content.decode(),
            r"/recuperar-senha/[^\"'\s]+/[^\"'\s]+/",
        )
        delay.assert_called_once_with(str(conta.pk))
        conta.refresh_from_db()
        self.assertEqual(conta.password, hash_antes)
        self.assertTrue(conta.check_password(SENHA))
        self.assertEqual(reverse("recuperar_senha"), "/recuperar-senha/")

    def test_unknown_email_does_not_enqueue(self):
        with patch("contas.views.preparar_link_de_recuperacao.delay") as delay:
            response = self.client.post(
                "/recuperar-senha/",
                {"email": "ninguem@exemplo.com"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MENSAGEM_RECUPERACAO)
        delay.assert_not_called()

    def test_task_logs_the_link_and_the_new_password_replaces_the_old_one(self):
        conta = criar_conta()
        buffer = StringIO()
        with redirect_stdout(buffer):
            link = preparar_link_de_recuperacao(str(conta.pk))

        self.assertRegex(link, r"^/recuperar-senha/[^/]+/[^/]+/$")
        self.assertEqual(
            buffer.getvalue(),
            f"recuperacao de senha conta={conta.pk} link={link}\n",
        )
        self.assertTrue(conta.check_password(SENHA))

        pagina = self.client.get(link)
        self.assertEqual(pagina.status_code, 200)
        self.assertContains(pagina, 'name="senha"')
        self.assertContains(pagina, STYLESHEET)
        self.assertNotContains(pagina, MENSAGEM_LINK)
        self.assertTrue(_formulario_volta_ao_caminho(pagina, link))

        resposta = self.client.post(link, {"senha": SENHA_NOVA})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta["Location"], "/entrar/")
        conta.refresh_from_db()
        self.assertTrue(conta.check_password(SENHA_NOVA))
        self.assertFalse(conta.check_password(SENHA))

        antigo = Client().post(
            "/entrar/",
            {"email": conta.email, "senha": SENHA},
        )
        self.assertEqual(antigo.status_code, 200)
        self.assertContains(antigo, MENSAGEM_LOGIN)
        self.assertNotIn("sessionid", antigo.cookies)

        novo = Client().post(
            "/entrar/",
            {"email": conta.email, "senha": SENHA_NOVA},
        )
        self.assertEqual(novo.status_code, 302)
        self.assertEqual(novo["Location"], "/area/")
        area = Client()
        area.cookies = novo.cookies
        aberta = area.get("/area/")
        self.assertEqual(aberta.status_code, 200)
        self.assertContains(aberta, "<h1>Área do cliente</h1>", html=True)
        self.assertContains(aberta, "Ana Lima")
        self.assertEqual(aberta.wsgi_request.user.pk, conta.pk)

        usado = self.client.post(link, {"senha": "outra-senha-9"})
        self.assertEqual(usado.status_code, 200)
        self.assertContains(usado, MENSAGEM_LINK)
        conta.refresh_from_db()
        self.assertTrue(conta.check_password(SENHA_NOVA))
        self.assertFalse(conta.check_password("outra-senha-9"))

    def test_bad_token_does_not_change_the_password(self):
        conta = criar_conta()
        hash_antes = conta.password
        buffer = StringIO()
        with redirect_stdout(buffer):
            link = preparar_link_de_recuperacao(str(conta.pk))
        uidb64 = link.strip("/").split("/")[1]

        for caminho in (
            "/recuperar-senha/nao-existe/token-ruim/",
            f"/recuperar-senha/{uidb64}/token-ruim/",
        ):
            with self.subTest(caminho=caminho):
                for metodo in ("get", "post"):
                    cliente = Client()
                    resposta = getattr(cliente, metodo)(
                        caminho,
                        {"senha": "outra-senha-9"},
                    )
                    self.assertEqual(resposta.status_code, 200)
                    self.assertContains(resposta, MENSAGEM_LINK)
                    self.assertNotContains(resposta, 'name="senha"')
                    conta.refresh_from_db()
                    self.assertEqual(conta.password, hash_antes)
                    self.assertTrue(conta.check_password(SENHA))

    def test_new_password_uses_the_existing_validators(self):
        conta = criar_conta()
        buffer = StringIO()
        with redirect_stdout(buffer):
            link = preparar_link_de_recuperacao(str(conta.pk))
        hash_antes = conta.password
        casos = (
            ("ab-cde1", "pelo menos 8 caracteres"),
            ("password", "Esta senha é muito comum."),
            ("9081726354", "Esta senha é inteiramente numérica."),
            ("ana@exemplo.com", "A senha é muito parecida com e-mail"),
        )
        for senha, mensagem in casos:
            with self.subTest(senha=senha):
                resposta = self.client.post(link, {"senha": senha})
                erros = resposta.context["form"].errors["senha"]
                self.assertEqual(resposta.status_code, 200)
                self.assertNotContains(resposta, MENSAGEM_LINK)
                self.assertTrue(any(mensagem in erro for erro in erros), erros)
                conta.refresh_from_db()
                self.assertEqual(conta.password, hash_antes)

        self.assertTrue(conta.check_password(SENHA))

    def test_posts_without_csrf_token_are_rejected(self):
        conta = criar_conta()
        buffer = StringIO()
        with redirect_stdout(buffer):
            link = preparar_link_de_recuperacao(str(conta.pk))
        casos = (
            ("/entrar/", {"email": conta.email, "senha": SENHA}),
            ("/sair/", {}),
            ("/recuperar-senha/", {"email": conta.email}),
            (link, {"senha": SENHA_NOVA}),
        )
        for caminho, dados in casos:
            with self.subTest(caminho=caminho):
                resposta = Client(enforce_csrf_checks=True).post(caminho, dados)
                self.assertEqual(resposta.status_code, 403)
        conta.refresh_from_db()
        self.assertTrue(conta.check_password(SENHA))
        recusa = Client().post(
            "/entrar/",
            {"email": conta.email, "senha": SENHA_NOVA},
        )
        self.assertNotEqual(recusa.status_code, 302)

    def test_csrf_token_from_each_form_accepts_the_post(self):
        conta = criar_conta()
        cliente = Client(enforce_csrf_checks=True)

        entrada = cliente.get("/entrar/")
        login = cliente.post(
            "/entrar/",
            {
                "email": conta.email,
                "senha": SENHA,
                "csrfmiddlewaretoken": _token_csrf(entrada),
            },
        )
        self.assertEqual(login.status_code, 302)

        area = cliente.get("/area/")
        saida = cliente.post(
            "/sair/",
            {"csrfmiddlewaretoken": _token_csrf(area)},
        )
        self.assertEqual(saida.status_code, 302)

        pedido = cliente.get("/recuperar-senha/")
        with patch("contas.views.preparar_link_de_recuperacao.delay"):
            recuperacao = cliente.post(
                "/recuperar-senha/",
                {
                    "email": conta.email,
                    "csrfmiddlewaretoken": _token_csrf(pedido),
                },
            )
        self.assertEqual(recuperacao.status_code, 200)
        self.assertContains(recuperacao, MENSAGEM_RECUPERACAO)

        buffer = StringIO()
        with redirect_stdout(buffer):
            link = preparar_link_de_recuperacao(str(conta.pk))
        pagina = cliente.get(link)
        nova = cliente.post(
            link,
            {
                "senha": SENHA_NOVA,
                "csrfmiddlewaretoken": _token_csrf(pagina),
            },
        )
        self.assertEqual(nova.status_code, 302)

    def test_recovery_page_uses_the_light_base(self):
        resposta = self.client.get("/recuperar-senha/")
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, STYLESHEET)
        self.assertContains(resposta, 'name="email"')
        self.assertContains(resposta, 'action="/recuperar-senha/"')
        self.assertNotContains(resposta, 'class="dark"')
        self.assertNotContains(resposta, 'data-theme="dark"')
