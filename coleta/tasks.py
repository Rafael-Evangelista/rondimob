"""Recorded collection. Each source is its own task and does not fetch a URL."""

import json
from pathlib import Path

from celery import shared_task

from anuncios.gravar import gravar
from coleta.models import Falha
from coleta.parser import analisar

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "zap-exemplo.json"
FIXTURE_VIVA_REAL = (
    Path(__file__).resolve().parent / "fixtures" / "viva-real-exemplo.json"
)
FIXTURE_OLX = Path(__file__).resolve().parent / "fixtures" / "olx-exemplo.json"


@shared_task(name="coleta.tasks.coletar_zap", queue="zap")
def coletar_zap(payloads=None):
    """Upsert recorded ZAP payloads. With no argument, read the fixture file."""
    try:
        itens = _carregar(payloads, FIXTURE)
        for item in itens:
            gravar(analisar(item, "zap"))
    except Exception as exc:
        Falha.objects.create(fonte="zap", mensagem=str(exc))
        print(f"coleta zap falha: {exc}", flush=True)
        return None
    print(f"coleta zap gravou {len(itens)}", flush=True)
    return len(itens)


@shared_task(name="coleta.tasks.coletar_viva_real", queue="viva-real")
def coletar_viva_real(payloads=None):
    """Upsert recorded Viva Real payloads. With no argument, read the fixture file."""
    try:
        itens = _carregar(payloads, FIXTURE_VIVA_REAL)
        for item in itens:
            gravar(analisar(item, "viva-real"))
    except Exception as exc:
        Falha.objects.create(fonte="viva-real", mensagem=str(exc))
        print(f"coleta viva-real falha: {exc}", flush=True)
        return None
    print(f"coleta viva-real gravou {len(itens)}", flush=True)
    return len(itens)


@shared_task(name="coleta.tasks.coletar_olx", queue="olx")
def coletar_olx(payloads=None):
    """Upsert recorded OLX payloads. With no argument, read the fixture file."""
    try:
        itens = _carregar(payloads, FIXTURE_OLX)
        for item in itens:
            gravar(analisar(item, "olx"))
    except Exception as exc:
        Falha.objects.create(fonte="olx", mensagem=str(exc))
        print(f"coleta olx falha: {exc}", flush=True)
        return None
    print(f"coleta olx gravou {len(itens)}", flush=True)
    return len(itens)


def _carregar(payloads, fixture):
    if payloads is None:
        payloads = json.loads(fixture.read_text(encoding="utf-8"))
    if isinstance(payloads, dict):
        return [payloads]
    return list(payloads)
