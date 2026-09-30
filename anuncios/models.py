import uuid

from django.db import models


class Anuncio(models.Model):
    """One listing in the shared corpus. It has no account owner."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fonte = models.CharField(max_length=32)
    identificador_externo = models.CharField(max_length=255, blank=True, default="")
    url = models.TextField()
    titulo = models.TextField(blank=True, default="")
    endereco = models.TextField(blank=True, default="")
    descricao = models.TextField(blank=True, default="")
    preco = models.DecimalField(max_digits=14, decimal_places=2)
    area = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    quartos = models.IntegerField(blank=True, null=True)
    banheiros = models.IntegerField(blank=True, null=True)
    vagas = models.IntegerField(blank=True, null=True)
    cidade = models.CharField(max_length=64, blank=True, default="")
    bairro = models.CharField(max_length=255, blank=True, default="")
    tipo = models.CharField(max_length=64, blank=True, default="")
    imobiliaria = models.CharField(max_length=255, blank=True, default="")
    coletado_em = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["fonte", "identificador_externo"],
                condition=~models.Q(identificador_externo=""),
                name="anuncio_fonte_e_id_externo",
            ),
            models.UniqueConstraint(
                fields=["fonte", "url"],
                condition=models.Q(identificador_externo=""),
                name="anuncio_fonte_e_url_sem_id",
            ),
        ]


class Preco(models.Model):
    """One numeric price. A new row exists only when that number changes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anuncio = models.ForeignKey(
        Anuncio,
        on_delete=models.CASCADE,
        related_name="precos",
    )
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    coletado_em = models.DateTimeField()
