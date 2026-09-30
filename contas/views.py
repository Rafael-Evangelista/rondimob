from django.contrib.auth import login
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from contas.forms import MENSAGEM_EMAIL_EM_USO, CriarContaForm
from contas.models import Conta


def portal(request):
    return render(request, "contas/portal.html")


def entrar(request):
    return render(request, "contas/entrar.html")


def criar_conta(request):
    if request.method == "POST":
        form = CriarContaForm(request.POST)
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
    return render(request, "contas/area.html", {"conta": request.user})
