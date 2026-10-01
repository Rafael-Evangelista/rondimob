"""The only upsert of a listing and its price history."""

from datetime import datetime, timezone

from django.db import transaction

from anuncios.models import Anuncio, Preco

_CAMPOS = (
    "url",
    "titulo",
    "endereco",
    "descricao",
    "area",
    "quartos",
    "banheiros",
    "vagas",
    "cidade",
    "bairro",
    "tipo",
    "imobiliaria",
)


def gravar(dados):
    """Insert a listing or refresh it. The same numeric price only moves ``coletado_em``."""
    agora = datetime.now(timezone.utc)
    with transaction.atomic():
        anuncio = _buscar(dados)
        if anuncio is None:
            anuncio = Anuncio.objects.create(
                fonte=dados["fonte"],
                identificador_externo=dados["identificador_externo"],
                preco=dados["preco"],
                coletado_em=agora,
                **{campo: dados[campo] for campo in _CAMPOS},
            )
            Preco.objects.create(
                anuncio=anuncio,
                valor=dados["preco"],
                coletado_em=agora,
            )
            return anuncio
        if anuncio.preco == dados["preco"]:
            anuncio.coletado_em = agora
            anuncio.save(update_fields=["coletado_em"])
            return anuncio
        for campo in _CAMPOS:
            setattr(anuncio, campo, dados[campo])
        anuncio.preco = dados["preco"]
        anuncio.coletado_em = agora
        anuncio.save()
        Preco.objects.create(
            anuncio=anuncio,
            valor=dados["preco"],
            coletado_em=agora,
        )
        return anuncio


def _buscar(dados):
    fonte = dados["fonte"]
    externo = dados["identificador_externo"]
    if externo:
        return (
            Anuncio.objects.filter(fonte=fonte, identificador_externo=externo)
            .order_by("id")
            .first()
        )
    return (
        Anuncio.objects.filter(
            fonte=fonte,
            url=dados["url"],
            identificador_externo="",
        )
        .order_by("id")
        .first()
    )
