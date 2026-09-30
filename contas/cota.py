"""Free-trial gate. ``aceitar_pesquisa`` is the only writer of the counter."""

from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from contas.isolamento import definir_conta
from contas.models import Conta

# Named here on purpose. The window is calendar days in this zone.
FUSO = ZoneInfo("America/Sao_Paulo")
LIMITE_DE_PESQUISAS = 10
DIAS_ATE_O_ULTIMO_DIA_ABERTO = 13


def data_de_criacao(conta):
    """Creation calendar date in America/Sao_Paulo. That date is day 1."""
    return conta.criada_em.astimezone(FUSO).date()


def ultimo_dia_aberto(conta):
    """Last calendar date that still accepts a search. The next date is blocked."""
    return data_de_criacao(conta) + timedelta(days=DIAS_ATE_O_ULTIMO_DIA_ABERTO)


def pesquisas_restantes(conta):
    usadas = conta.pesquisas_gratis_usadas
    if usadas >= LIMITE_DE_PESQUISAS:
        return 0
    return LIMITE_DE_PESQUISAS - usadas


def nomes_de_radar(conta):
    """Radar names for this account. Empty until a later epic stores radars."""
    return []


def pode_pesquisar(conta):
    return _aberto(conta)


def pode_favoritar(conta):
    return _aberto(conta)


def pode_configurar_alerta(conta):
    return _aberto(conta)


def aceitar_pesquisa(conta):
    """Spend one free search, or return false without writing when blocked."""
    with transaction.atomic():
        definir_conta(conta.pk)
        atual = Conta.objects.select_for_update().get(pk=conta.pk)
        if not _aberto(atual):
            conta.pesquisas_gratis_usadas = atual.pesquisas_gratis_usadas
            return False
        atual.pesquisas_gratis_usadas += 1
        atual.save(update_fields=["pesquisas_gratis_usadas"])
        conta.pesquisas_gratis_usadas = atual.pesquisas_gratis_usadas
        return True


def _hoje():
    return timezone.now().astimezone(FUSO).date()


def _aberto(conta):
    if conta.pesquisas_gratis_usadas >= LIMITE_DE_PESQUISAS:
        return False
    return _hoje() <= ultimo_dia_aberto(conta)
