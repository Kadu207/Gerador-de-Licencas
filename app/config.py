from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    license_server_host: str = "127.0.0.1"
    license_server_port: int = 8195
    trust_proxy: bool = False
    public_base_url: str = ""
    secret_key: str = "change-me-in-production-use-long-random-string"
    admin_username: str = "admin"
    admin_password: str = "Admin@Licencas2026!"
    local_database_url: str = "sqlite:///./data/gerador_licencas.db"
    sync_remote_enabled: bool = False
    erp_database_url: str = ""
    lab_database_url: str = ""
    lab_schema: str = "dental_lab"
    erp_api_base: str = "http://127.0.0.1/api"
    erp_admin_user: str = "admin"
    erp_admin_password: str = ""
    block_after_days: int = 30
    cancel_after_days: int = 45
    product_api_key: str = ""
    lab_auto_trial_days: int = 30
    access_token_ttl_minutes: int = 480

    # Email (alertas)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "licencas@inovatitech.com.br"
    smtp_use_tls: bool = True

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_currency: str = "brl"

    # NFS-e prefeitura (preencher quando credenciais disponíveis)
    nfse_enabled: bool = False
    nfse_api_url: str = ""
    nfse_cert_path: str = ""
    nfse_service_code: str = ""

    # Receita Federal / BrasilAPI
    receita_api_base: str = "https://brasilapi.com.br/api"


settings = Settings()
