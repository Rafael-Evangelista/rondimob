import uuid

from django.conf import settings
from django.db import models, transaction
from django.db.models.functions import Now
from django.utils import timezone

from contas.isolamento import definir_conta


class Radar(models.Model):
    """Filters one account wants to monitor. The id exposed outside is a UUID."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conta = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="radares",
    )
    imobiliaria = models.CharField(max_length=255, blank=True, default="")
    cidade = models.CharField(max_length=64)
    bairro = models.CharField(max_length=255, blank=True, default="")
    tipo = models.CharField(max_length=64, blank=True, default="")
    preco_minimo = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    preco_maximo = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    area_minima = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    area_maxima = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    quartos_minimos = models.PositiveIntegerField(blank=True, null=True)
    vagas_minimas = models.PositiveIntegerField(blank=True, null=True)
    criado_em = models.DateTimeField(default=timezone.now, db_default=Now())

    def save(self, **kwargs):
        if self.id is None:
            self.id = uuid.uuid4()
        using = kwargs.get("using")
        with transaction.atomic(using=using):
            definir_conta(self.conta_id, using=using)
            super().save(**kwargs)

    @property
    def rotulo(self):
        """City, type, and announcing agency, skipping blanks."""
        partes = (self.cidade, self.tipo, self.imobiliaria)
        return " · ".join(parte for parte in partes if parte)
