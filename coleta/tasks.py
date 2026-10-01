"""ZAP collection. It reads a recorded payload and does not fetch a URL."""

import json
from pathlib import Path

from celery import shared_task

from anuncios.gravar import gravar
from coleta.models import Falha
from coleta.parser import analisar

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "zap-exemplo.json"


@shared_task(name="coleta.tasks.coletar_zap", queue="zap")
def coletar_zap(payloads=None):
    """Upsert recorded ZAP payloads. With no argument, read the fixture file."""
    try:
        itens = _carregar(payloads)
        for item in itens:
            gravar(analisar(item))
    except Exception as exc:
        Falha.objects.create(fonte="zap", mensagem=str(exc))
        print(f"coleta zap falha: {exc}", flush=True)
        return None
    print(f"coleta zap gravou {len(itens)}", flush=True)
    return len(itens)


def _carregar(payloads):
    if payloads is None:
        payloads = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if isinstance(payloads, dict):
        return [payloads]
    return list(payloads)
