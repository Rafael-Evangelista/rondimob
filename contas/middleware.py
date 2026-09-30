from django.contrib.auth import SESSION_KEY
from django.db import transaction

from contas.isolamento import definir_conta


class IsolamentoDaContaMiddleware:
    """Open one transaction and set ``app.conta_id`` before authentication."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with transaction.atomic():
            conta_id = request.session.get(SESSION_KEY) or ""
            definir_conta(conta_id)
            return self.get_response(request)
