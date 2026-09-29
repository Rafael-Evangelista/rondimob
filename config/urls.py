from django.urls import path

from contas import views

urlpatterns = [
    path("", views.portal, name="portal"),
    path("criar-conta/", views.criar_conta, name="criar_conta"),
    path("area/", views.area, name="area"),
    path("entrar/", views.entrar, name="entrar"),
]
