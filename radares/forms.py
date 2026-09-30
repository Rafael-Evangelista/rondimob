import unicodedata

from django import forms
from django.core.exceptions import ValidationError

from radares.models import Radar

MENSAGEM_CIDADE = (
    "Informe Santo André, São Bernardo do Campo, São Caetano do Sul ou Diadema."
)
MENSAGEM_FAIXA = "O máximo não pode ser menor que o mínimo."

_CIDADES = {
    "santo andre": "Santo André",
    "sao bernardo do campo": "São Bernardo do Campo",
    "sao caetano do sul": "São Caetano do Sul",
    "diadema": "Diadema",
}


def _chave(valor):
    texto = unicodedata.normalize("NFKD", valor or "")
    sem_acento = "".join(letra for letra in texto if not unicodedata.combining(letra))
    return " ".join(sem_acento.casefold().split())


def _texto(valor):
    return (valor or "").strip().casefold()


class RadarForm(forms.ModelForm):
    class Meta:
        model = Radar
        fields = [
            "imobiliaria",
            "cidade",
            "bairro",
            "tipo",
            "preco_minimo",
            "preco_maximo",
            "area_minima",
            "area_maxima",
            "quartos_minimos",
            "vagas_minimas",
        ]
        labels = {
            "imobiliaria": "Imobiliária anunciante",
            "cidade": "Cidade",
            "bairro": "Bairro",
            "tipo": "Tipo",
            "preco_minimo": "Preço mínimo",
            "preco_maximo": "Preço máximo",
            "area_minima": "Área mínima",
            "area_maxima": "Área máxima",
            "quartos_minimos": "Quartos mínimos",
            "vagas_minimas": "Vagas mínimas",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome in (
            "preco_minimo",
            "preco_maximo",
            "area_minima",
            "area_maxima",
            "quartos_minimos",
            "vagas_minimas",
        ):
            self.fields[nome].required = False
            self.fields[nome].localize = False
        for nome in ("imobiliaria", "bairro", "tipo"):
            self.fields[nome].required = False

    def clean_imobiliaria(self):
        return _texto(self.cleaned_data.get("imobiliaria"))

    def clean_bairro(self):
        return _texto(self.cleaned_data.get("bairro"))

    def clean_tipo(self):
        return _texto(self.cleaned_data.get("tipo"))

    def clean_cidade(self):
        canonica = _CIDADES.get(_chave(self.cleaned_data.get("cidade")))
        if canonica is None:
            raise ValidationError(MENSAGEM_CIDADE)
        return canonica

    def clean(self):
        cleaned = super().clean()
        self._rejeitar_faixa(cleaned, "preco_minimo", "preco_maximo")
        self._rejeitar_faixa(cleaned, "area_minima", "area_maxima")
        return cleaned

    def _rejeitar_faixa(self, cleaned, minimo, maximo):
        baixo = cleaned.get(minimo)
        alto = cleaned.get(maximo)
        if baixo is not None and alto is not None and alto < baixo:
            self.add_error(maximo, MENSAGEM_FAIXA)

    def save(self, conta):
        radar = super().save(commit=False)
        radar.conta = conta
        radar.save()
        return radar
