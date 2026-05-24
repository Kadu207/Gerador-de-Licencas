"""
Adapter NFS-e — API da prefeitura.

Aguardando documentação e credenciais do usuário (URL, certificado A1, código de serviço).
Implementação stub para homologação futura.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger("license-nfse")


@dataclass
class NfseResult:
    numero: str
    protocolo: str
    verification_url: str
    xml_content: str
    status: str


class PrefeituraNfseAdapter:
    """Interface para emissão de NFS-e via API municipal."""

    def __init__(self) -> None:
        self.api_url = settings.nfse_api_url
        self.cert_path = settings.nfse_cert_path
        self.service_code = settings.nfse_service_code

    @property
    def configured(self) -> bool:
        return settings.nfse_enabled and bool(self.api_url)

    def emit_nfse(
        self,
        *,
        client_document: str,
        client_name: str,
        amount: float,
        description: str,
    ) -> NfseResult:
        if not self.configured:
            logger.warning("NFS-e não configurada — retornando stub")
            return NfseResult(
                numero="PENDENTE",
                protocolo="",
                verification_url="",
                xml_content="<!-- aguardando credenciais prefeitura -->",
                status="pending_credentials",
            )
        raise NotImplementedError(
            "Implementar após receber WSDL/OpenAPI e certificado da prefeitura. "
            "Ver docs/INTEGRACAO-NFSE-PREFEITURA.md"
        )

    def cancel_nfse(self, numero: str, motivo: str) -> bool:
        if not self.configured:
            return False
        raise NotImplementedError("cancel_nfse — aguardando documentação prefeitura")

    def get_status(self, protocolo: str) -> str:
        if not self.configured:
            return "pending_credentials"
        raise NotImplementedError("get_status — aguardando documentação prefeitura")
