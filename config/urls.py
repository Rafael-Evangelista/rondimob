from django.urls import path

from contas import views
from radares import views as radares_views

urlpatterns = [
    path("", views.portal, name="portal"),
    path("criar-conta/", views.criar_conta, name="criar_conta"),
    path("area/", views.area, name="area"),
    path("area/radares/novo/", radares_views.novo, name="novo_radar"),
    path(
        "area/radares/<uuid:radar_id>/",
        radares_views.editar,
        name="editar_radar",
    ),
    path("area/plano/", views.ativar_plano, name="ativar_plano"),
    path("area/credito/", views.recarregar_credito, name="recarregar_credito"),
    path("entrar/", views.entrar, name="entrar"),
    path("sair/", views.sair, name="sair"),
    path("recuperar-senha/", views.recuperar_senha, name="recuperar_senha"),
    path(
        "recuperar-senha/<uidb64>/<token>/",
        views.definir_senha,
        name="definir_senha",
    ),
]
