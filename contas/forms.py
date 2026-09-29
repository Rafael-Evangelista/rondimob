import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from contas.models import Conta, normalizar_email

MENSAGEM_TIPO = "Escolha corretor ou imobiliária."
MENSAGEM_CRECI = "Informe o CRECI no formato número e UF."
MENSAGEM_CNPJ = (
    "Informe um CNPJ com 14 dígitos e dígitos verificadores válidos."
)
MENSAGEM_EMAIL_EM_USO = "Este e-mail já está em uso."

_UFS = frozenset(
    {
        "AC",
        "AL",
        "AP",
        "AM",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MT",
        "MS",
        "MG",
        "PA",
        "PB",
        "PR",
        "PE",
        "PI",
        "RJ",
        "RN",
        "RS",
        "RO",
        "RR",
        "SC",
        "SP",
        "SE",
        "TO",
    }
)
_CRECI_RE = re.compile(r"^(\d+)[\s./\-]*([FJ])?[\s./\-]*([A-Z]{2})$")
_PESOS_CNPJ_1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_PESOS_CNPJ_2 = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def normalizar_creci(valor):
    """Digits, an optional F or J, and a Brazilian UF. Separators are optional."""
    texto = (valor or "").strip().upper()
    correspondencia = _CRECI_RE.fullmatch(texto)
    if correspondencia is None:
        return None
    numero, letra, uf = correspondencia.groups()
    if uf not in _UFS:
        return None
    if letra:
        return f"{numero}-{letra}-{uf}"
    return f"{numero}-{uf}"


def _digito_cnpj(base, pesos):
    soma = sum(int(digito) * peso for digito, peso in zip(base, pesos))
    resto = soma % 11
    if resto < 2:
        return "0"
    return str(11 - resto)


def normalizar_cnpj(valor):
    """14 digits and official check digits. Punctuation is ignored."""
    bruto = re.sub(r"[^0-9A-Za-z]", "", valor or "")
    if not bruto.isdigit() or len(bruto) != 14:
        return None
    if len(set(bruto)) == 1:
        return None
    primeiro = _digito_cnpj(bruto[:12], _PESOS_CNPJ_1)
    segundo = _digito_cnpj(bruto[:12] + primeiro, _PESOS_CNPJ_2)
    if bruto[12:] != primeiro + segundo:
        return None
    return bruto


class CriarContaForm(forms.Form):
    tipo = forms.ChoiceField(
        label="Tipo",
        choices=Conta.TIPO_CHOICES,
        widget=forms.RadioSelect,
        error_messages={
            "required": MENSAGEM_TIPO,
            "invalid_choice": MENSAGEM_TIPO,
        },
    )
    nome = forms.CharField(label="Nome", required=False, max_length=255)
    email = forms.EmailField(
        label="E-mail",
        error_messages={"required": "Informe o e-mail."},
    )
    telefone = forms.CharField(label="Telefone", required=False, max_length=40)
    senha = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        error_messages={"required": "Informe a senha."},
    )
    creci = forms.CharField(label="CRECI", required=False, max_length=64)
    razao_social = forms.CharField(
        label="Razão social",
        required=False,
        max_length=255,
    )
    cnpj = forms.CharField(label="CNPJ", required=False, max_length=32)
    responsavel = forms.CharField(label="Responsável", required=False, max_length=255)

    def clean_email(self):
        email = normalizar_email(self.cleaned_data.get("email"))
        if email and Conta.objects.filter(email=email).exists():
            raise forms.ValidationError(MENSAGEM_EMAIL_EM_USO)
        return email

    def _exigir_texto(self, campo, mensagem):
        if campo in self.errors:
            return ""
        valor = (self.cleaned_data.get(campo) or "").strip()
        if not valor:
            self.add_error(campo, mensagem)
            return ""
        self.cleaned_data[campo] = valor
        return valor

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo")
        if tipo == Conta.TIPO_CORRETOR:
            self._exigir_texto("nome", "Informe o nome.")
            self._exigir_texto("telefone", "Informe o telefone.")
            if "creci" not in self.errors:
                creci = normalizar_creci(cleaned.get("creci"))
                if creci is None:
                    self.add_error("creci", MENSAGEM_CRECI)
                else:
                    cleaned["creci"] = creci
            cleaned["razao_social"] = ""
            cleaned["cnpj"] = ""
            cleaned["responsavel"] = ""
        elif tipo == Conta.TIPO_IMOBILIARIA:
            self._exigir_texto("razao_social", "Informe a razão social.")
            self._exigir_texto("responsavel", "Informe o responsável.")
            self._exigir_texto("telefone", "Informe o telefone.")
            if "cnpj" not in self.errors:
                cnpj = normalizar_cnpj(cleaned.get("cnpj"))
                if cnpj is None:
                    self.add_error("cnpj", MENSAGEM_CNPJ)
                else:
                    cleaned["cnpj"] = cnpj
            cleaned["nome"] = ""
            cleaned["creci"] = ""

        senha = cleaned.get("senha")
        if senha and "senha" not in self.errors:
            candidato = Conta(email=cleaned.get("email") or "")
            try:
                validate_password(senha, candidato)
            except ValidationError as exc:
                self.add_error("senha", exc)
        return cleaned

    def save(self):
        dados = self.cleaned_data
        return Conta.objects.create_user(
            email=dados["email"],
            password=dados["senha"],
            tipo=dados["tipo"],
            nome=dados.get("nome") or "",
            telefone=dados.get("telefone") or "",
            creci=dados.get("creci") or "",
            razao_social=dados.get("razao_social") or "",
            cnpj=dados.get("cnpj") or "",
            responsavel=dados.get("responsavel") or "",
        )
