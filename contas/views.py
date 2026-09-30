from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.http import require_POST

from contas.cota import (
    nomes_de_radar,
    pode_pesquisar,
    pesquisas_restantes,
    ultimo_dia_aberto,
)
from contas.forms import (
    MENSAGEM_EMAIL_EM_USO,
    CriarContaForm,
    DefinirSenhaForm,
    EntrarForm,
    RecuperarSenhaForm,
)
from contas.isolamento import definir_conta, definir_email_de_login
from contas.models import Conta, normalizar_email
from contas.tasks import preparar_link_de_recuperacao

MENSAGEM_LOGIN = "E-mail ou senha incorretos."
MENSAGEM_LINK_INVALIDO = "Este link não vale mais."


def portal(request):
    return render(request, "contas/portal.html")


def entrar(request):
    if request.method == "POST":
        form = EntrarForm(request.POST)
        if form.is_valid():
            definir_email_de_login(form.cleaned_data["email"])
            conta = authenticate(
                request,
                username=form.cleaned_data["email"],
                password=form.cleaned_data["senha"],
            )
            if conta is None:
                form.add_error(None, MENSAGEM_LOGIN)
            else:
                login(request, conta)
                return redirect("area")
    else:
        form = EntrarForm()
    return render(request, "contas/entrar.html", {"form": form})


@require_POST
def sair(request):
    logout(request)
    return redirect("entrar")


def criar_conta(request):
    if request.method == "POST":
        form = CriarContaForm(request.POST)
        definir_email_de_login(normalizar_email(request.POST.get("email", "")))
        if form.is_valid():
            try:
                with transaction.atomic():
                    conta = form.save()
            except IntegrityError:
                email = form.cleaned_data.get("email")
                if email and Conta.objects.filter(email=email).exists():
                    form.add_error("email", MENSAGEM_EMAIL_EM_USO)
                else:
                    raise
            else:
                login(
                    request,
                    conta,
                    backend="django.contrib.auth.backends.ModelBackend",
                )
                return redirect("area")
    else:
        form = CriarContaForm()
    return render(request, "contas/criar_conta.html", {"form": form})


def area(request):
    if not request.user.is_authenticated:
        return redirect("entrar")
    conta = request.user
    aberto = pode_pesquisar(conta)
    contexto = {"conta": conta, "trial_aberto": aberto}
    if aberto:
        contexto["pesquisas_restantes"] = pesquisas_restantes(conta)
        contexto["ultimo_dia"] = ultimo_dia_aberto(conta)
    else:
        contexto["radares"] = nomes_de_radar(conta)
    return render(request, "contas/area.html", contexto)


def recuperar_senha(request):
    if request.method == "POST":
        form = RecuperarSenhaForm(request.POST)
        if form.is_valid():
            definir_email_de_login(form.cleaned_data["email"])
            conta = Conta.objects.filter(email=form.cleaned_data["email"]).first()
            if conta is not None:
                preparar_link_de_recuperacao.delay(str(conta.pk))
            return render(
                request,
                "contas/recuperar_senha.html",
                {"confirmado": True},
            )
    else:
        form = RecuperarSenhaForm()
    return render(request, "contas/recuperar_senha.html", {"form": form})


def _conta_pelo_uidb64(uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        definir_conta(uid)
        return Conta.objects.get(pk=uid)
    except (
        Conta.DoesNotExist,
        ValidationError,
        ValueError,
        TypeError,
        OverflowError,
    ):
        return None


def definir_senha(request, uidb64, token):
    conta = _conta_pelo_uidb64(uidb64)
    if conta is None or not PasswordResetTokenGenerator().check_token(conta, token):
        return render(
            request,
            "contas/definir_senha.html",
            {"invalido": True, "mensagem": MENSAGEM_LINK_INVALIDO},
        )
    if request.method == "POST":
        form = DefinirSenhaForm(conta, request.POST)
        if form.is_valid():
            form.save()
            return redirect("entrar")
    else:
        form = DefinirSenhaForm(conta)
    return render(request, "contas/definir_senha.html", {"form": form})
