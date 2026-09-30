"""Map a recorded payload. This module does not fetch a URL."""

from decimal import Decimal, InvalidOperation


class ErroDePayload(Exception):
    """The payload cannot be stored."""


def analisar(payload):
    """Return the normalized listing fields for one recorded object."""
    if not isinstance(payload, dict):
        raise ErroDePayload("payload inválido")
    url = str(payload.get("url") or "").strip()
    if not url:
        raise ErroDePayload("payload sem url")
    if "preco" not in payload or payload.get("preco") is None:
        raise ErroDePayload("payload sem preço")
    externo = payload.get("identificador_externo", payload.get("id"))
    return {
        "fonte": "zap",
        "identificador_externo": str(externo or "").strip(),
        "url": url,
        "titulo": _limpo(payload.get("titulo")),
        "endereco": _limpo(payload.get("endereco")),
        "descricao": _limpo(payload.get("descricao")),
        "preco": preco_numerico(payload.get("preco")),
        "area": _area(payload.get("area")),
        "quartos": _inteiro(payload.get("quartos")),
        "banheiros": _inteiro(payload.get("banheiros")),
        "vagas": _inteiro(payload.get("vagas")),
        "cidade": _texto(payload.get("cidade")),
        "bairro": _texto(payload.get("bairro")),
        "tipo": _texto(payload.get("tipo")),
        "imobiliaria": _texto(payload.get("imobiliaria")),
    }


def preco_numerico(valor):
    """Parse "R$ 650.000", "650 mil" and "650000" as the same numeric."""
    if isinstance(valor, bool) or valor is None:
        raise ErroDePayload("preço inválido")
    texto = str(valor).replace("\u00a0", " ").strip().casefold()
    texto = texto.replace("r$", "").strip()
    if texto.endswith("mil"):
        numero = _decimal_br(texto[: -len("mil")].strip()) * Decimal("1000")
    else:
        numero = _decimal_br(texto)
    return numero.quantize(Decimal("0.01"))


def _decimal_br(texto):
    texto = texto.replace(" ", "")
    if not texto:
        raise ErroDePayload("preço inválido")
    if "," in texto:
        inteiro, _, fracao = texto.partition(",")
        if not fracao.isdigit() or not inteiro.replace(".", "").isdigit():
            raise ErroDePayload("preço inválido")
        texto = inteiro.replace(".", "") + "." + fracao
    else:
        partes = texto.split(".")
        if (
            len(partes) > 1
            and partes[0].isdigit()
            and all(parte.isdigit() and len(parte) == 3 for parte in partes[1:])
        ):
            texto = "".join(partes)
    try:
        numero = Decimal(texto)
    except InvalidOperation as exc:
        raise ErroDePayload("preço inválido") from exc
    if not numero.is_finite():
        raise ErroDePayload("preço inválido")
    return numero


def _texto(valor):
    return str(valor or "").strip().casefold()


def _limpo(valor):
    return str(valor or "").strip()


def _inteiro(valor):
    if valor is None or valor == "":
        return None
    if isinstance(valor, bool):
        raise ErroDePayload("número inválido")
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError) as exc:
        raise ErroDePayload("número inválido") from exc


def _area(valor):
    if valor is None or valor == "":
        return None
    try:
        return Decimal(str(valor).strip())
    except InvalidOperation as exc:
        raise ErroDePayload("área inválida") from exc
