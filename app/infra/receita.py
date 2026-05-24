"""Validação de CPF/CNPJ e consulta Receita Federal via BrasilAPI."""
from __future__ import annotations

import re
import urllib.error
import urllib.request
import json

from app.config import settings

CPF_PATTERN = re.compile(r"^\d{11}$")
CNPJ_PATTERN = re.compile(r"^\d{14}$")


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def validate_cpf_format(cpf: str) -> bool:
    d = _digits(cpf)
    if not CPF_PATTERN.match(d) or d == d[0] * 11:
        return False
    for i in range(9, 11):
        weight = list(range(i + 1, 1, -1))
        total = sum(int(d[num]) * weight[num] for num in range(i))
        digit = (total * 10 % 11) % 10
        if int(d[i]) != digit:
            return False
    return True


def validate_cnpj_format(cnpj: str) -> bool:
    d = _digits(cnpj)
    if not CNPJ_PATTERN.match(d) or d == d[0] * 14:
        return False
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for length, weights in ((12, weights1), (13, weights2)):
        total = sum(int(d[i]) * weights[i] for i in range(length))
        digit = 11 - (total % 11)
        if digit >= 10:
            digit = 0
        if int(d[length]) != digit:
            return False
    return True


def validate_document(document_type: str, value: str) -> bool:
    if document_type == "cpf":
        return validate_cpf_format(value)
    return validate_cnpj_format(value)


def fetch_cnpj_receita(cnpj: str) -> dict | None:
    digits = _digits(cnpj)
    if not validate_cnpj_format(digits):
        return None
    url = f"{settings.receita_api_base.rstrip('/')}/cnpj/v1/{digits}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None
