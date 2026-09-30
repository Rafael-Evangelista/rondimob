import unicodedata
import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


def normalizar_email(email):
    """Lowercase the whole address so uniqueness does not depend on case."""
    texto = unicodedata.normalize("NFKC", (email or "").strip())
    return texto.lower()


class ContaManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not str(email or "").strip():
            raise ValueError("O e-mail é obrigatório.")
        conta = self.model(email=normalizar_email(email), **extra_fields)
        conta.set_password(password)
        conta.save(using=self._db)
        return conta

    def get_by_natural_key(self, username):
        return self.get(email=normalizar_email(username))


class Conta(AbstractBaseUser):
    TIPO_CORRETOR = "corretor"
    TIPO_IMOBILIARIA = "imobiliaria"
    TIPO_CHOICES = [
        (TIPO_CORRETOR, "Corretor"),
        (TIPO_IMOBILIARIA, "Imobiliária"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254, unique=True, verbose_name="e-mail")
    tipo = models.CharField(max_length=12, choices=TIPO_CHOICES)
    nome = models.CharField(max_length=255, blank=True, default="")
    telefone = models.CharField(max_length=40, blank=True, default="")
    creci = models.CharField(max_length=64, blank=True, default="")
    razao_social = models.CharField(max_length=255, blank=True, default="")
    cnpj = models.CharField(max_length=14, blank=True, default="")
    responsavel = models.CharField(max_length=255, blank=True, default="")

    objects = ContaManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, **kwargs):
        self.email = normalizar_email(self.email)
        super().save(**kwargs)

    @property
    def nome_exibicao(self):
        if self.tipo == self.TIPO_IMOBILIARIA:
            return self.razao_social
        return self.nome
