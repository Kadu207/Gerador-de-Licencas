"""Consulta CEP via ViaCEP."""
from __future__ import annotations

import urllib.error
import urllib.request
import json


def fetch_address_by_cep(cep: str) -> dict | None:
    digits = "".join(c for c in cep if c.isdigit())
    if len(digits) != 8:
        return None
    url = f"https://viacep.com.br/ws/{digits}/json/"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data.get("erro"):
            return None
        return {
            "logradouro": data.get("logradouro", ""),
            "bairro": data.get("bairro", ""),
            "cidade": data.get("localidade", ""),
            "uf": data.get("uf", ""),
            "cep": digits,
        }
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None
