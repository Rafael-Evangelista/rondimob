"""Search quota.

``aceitar_pesquisa`` is the only writer that spends a search. A paid plan
spends the month first and spends credit only after that quota is zero. An
account with no plan still spends ``pesquisas_gratis_usadas`` and never spends
credit. ``ativar_plano`` and ``recarregar_credito`` change stored state and do
not call a payment gateway.
"""

from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from contas.isolamento import definir_conta
from contas.models import Conta, Credito

# Named here on purpose. The window is calendar days in this zone.
FUSO = ZoneInfo("America/Sao_Paulo")
LIMITE_DE_PESQUISAS = 10
DIAS_ATE_O_ULTIMO_DIA_ABERTO = 13
PESQUISAS_DO_PLANO = {
    Conta.PLANO_PADRAO: 30,
    Conta.PLANO_PLUS: 100,
}
NOMES_DE_PLANO = {
    Conta.PLANO_PADRAO: "Padrão",
    Conta.PLANO_PLUS: "Plus",
}
PACOTE_DE_PESQUISAS = 10
PRECO_DO_PACOTE = Decimal("47.00")


def data_de_criacao(conta):
    """Creation calendar date in America/Sao_Paulo. That date is day 1."""
    return conta.criada_em.astimezone(FUSO).date()


def ultimo_dia_aberto(conta):
    """Last calendar date that still accepts a search. The next date is blocked."""
    return data_de_criacao(conta) + timedelta(days=DIAS_ATE_O_ULTIMO_DIA_ABERTO)


def plano_pago(conta):
    return conta.plano in PESQUISAS_DO_PLANO


def nome_do_plano(conta):
    return NOMES_DE_PLANO[conta.plano]


def pesquisas_restantes(conta):
    if plano_pago(conta):
        limite = PESQUISAS_DO_PLANO[conta.plano]
        return max(0, limite - _usadas_no_mes(conta))
    if not _aberto(conta):
        return 0
    return LIMITE_DE_PESQUISAS - conta.pesquisas_gratis_usadas


def nomes_de_radar(conta):
    """Labels for this account's radars, oldest first."""
    from radares.models import Radar

    return [
        radar.rotulo
        for radar in Radar.objects.filter(conta=conta).order_by("criado_em")
    ]


def resultados_gravados(conta):
    """Saved results for this account. Empty until a later epic stores them."""
    return []


def saldo_credito(conta):
    """Sum of remaining units. Credit stays until those units are spent."""
    total = Credito.objects.filter(conta=conta).aggregate(total=Sum("restante"))["total"]
    return total or 0


def pode_pesquisar(conta):
    if plano_pago(conta):
        if _usadas_no_mes(conta) < PESQUISAS_DO_PLANO[conta.plano]:
            return True
        return saldo_credito(conta) > 0
    return _aberto(conta)


def pode_favoritar(conta):
    if plano_pago(conta):
        return True
    return _aberto(conta)


def pode_configurar_alerta(conta):
    if plano_pago(conta):
        return True
    return _aberto(conta)


def aceitar_pesquisa(conta):
    """Spend one search, or return false without writing when blocked."""
    with transaction.atomic():
        definir_conta(conta.pk)
        atual = Conta.objects.select_for_update().get(pk=conta.pk)
        if plano_pago(atual):
            aceita = _gastar_mes(atual)
            if not aceita:
                aceita = _gastar_credito(atual)
        else:
            aceita = _gastar_gratis(atual)
        _copiar_cota(conta, atual)
        return aceita


def recarregar_credito(conta):
    """Store one package of 10 searches at R$ 47. Paid plans only."""
    with transaction.atomic():
        definir_conta(conta.pk)
        atual = Conta.objects.select_for_update().get(pk=conta.pk)
        if not plano_pago(atual):
            return False
        Credito.objects.create(
            conta=atual,
            preco=PRECO_DO_PACOTE,
            restante=PACOTE_DE_PESQUISAS,
        )
        return True


def ativar_plano(conta, plano):
    """Store Padrão or Plus. The first activation zeroes this month's counter."""
    if plano not in PESQUISAS_DO_PLANO:
        return False
    with transaction.atomic():
        definir_conta(conta.pk)
        atual = Conta.objects.select_for_update().get(pk=conta.pk)
        campos = ["plano"]
        if not atual.plano:
            atual.pesquisas_mes_usadas = 0
            atual.mes_da_cota = _primeiro_dia(_hoje())
            campos.extend(["pesquisas_mes_usadas", "mes_da_cota"])
        atual.plano = plano
        atual.save(update_fields=campos)
        _copiar_cota(conta, atual)
        return True


def _gastar_gratis(atual):
    if not _aberto(atual):
        return False
    atual.pesquisas_gratis_usadas += 1
    atual.save(update_fields=["pesquisas_gratis_usadas"])
    return True


def _gastar_mes(atual):
    mes = _primeiro_dia(_hoje())
    if atual.mes_da_cota != mes:
        atual.pesquisas_mes_usadas = 0
        atual.mes_da_cota = mes
    if atual.pesquisas_mes_usadas >= PESQUISAS_DO_PLANO[atual.plano]:
        return False
    atual.pesquisas_mes_usadas += 1
    atual.save(update_fields=["pesquisas_mes_usadas", "mes_da_cota"])
    return True


def _gastar_credito(atual):
    pacote = (
        Credito.objects.select_for_update()
        .filter(conta=atual, restante__gt=0)
        .order_by("criado_em", "id")
        .first()
    )
    if pacote is None:
        return False
    pacote.restante -= 1
    pacote.save(update_fields=["restante"])
    return True


def _copiar_cota(destino, origem):
    destino.plano = origem.plano
    destino.pesquisas_gratis_usadas = origem.pesquisas_gratis_usadas
    destino.pesquisas_mes_usadas = origem.pesquisas_mes_usadas
    destino.mes_da_cota = origem.mes_da_cota


def _usadas_no_mes(conta):
    # A different calendar month ignores the stored count. Leftovers do not carry.
    if conta.mes_da_cota != _primeiro_dia(_hoje()):
        return 0
    return conta.pesquisas_mes_usadas


def _hoje():
    return timezone.now().astimezone(FUSO).date()


def _primeiro_dia(dia):
    return dia.replace(day=1)


def _aberto(conta):
    if conta.pesquisas_gratis_usadas >= LIMITE_DE_PESQUISAS:
        return False
    return _hoje() <= ultimo_dia_aberto(conta)
