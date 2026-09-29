from django.urls import path

from contas import views

urlpatterns = [
    path("", views.portal, name="portal"),
    path("entrar/", views.entrar, name="entrar"),
]
