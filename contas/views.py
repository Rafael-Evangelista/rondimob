from django.shortcuts import render


def portal(request):
    return render(request, "contas/portal.html")


def entrar(request):
    return render(request, "contas/entrar.html")
