import uuid

from django.db import models
from django.utils import timezone


class Falha(models.Model):
    """One recorded collection failure. The listing is not left half-written."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fonte = models.CharField(max_length=32)
    mensagem = models.TextField()
    criada_em = models.DateTimeField(default=timezone.now)
