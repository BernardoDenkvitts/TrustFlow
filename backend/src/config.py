"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "TrustFlow"
    debug: bool = False

    # CORS
    frontend_url: str = "http://localhost:3000"
    allowed_origins: list[str] = [frontend_url, "http://localhost:8000"] 

    # Database
    database_url: str = (
        "postgresql+asyncpg://trustflow:trustflow@localhost:5432/trustflow"
    )

    # Blockchain
    rpc_url: str = "http://localhost:8545"
    chain_id: int = 31337  # Anvil default
    escrow_contract_address: str = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

    # Sync Worker
    sync_interval_seconds: int = 15
    confirmations: int = 2

    # Auth
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_path: str = "/auth"
    refresh_token_duration: int = int(24 * 60 * 60) * 15  # 15 days

    google_redirect_uri: str = "http://localhost:8000/api/auth/callback/google"
    google_client_id: str | None = "31283781970-m7535tn8c68qqp15bra89p4tn6uei76k.apps.googleusercontent.com"
    google_client_secret: str | None = "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"

    # Session Management
    max_sessions_per_user: int = 5
    session_cleanup_interval_seconds: int = 3600 * 6 # 6 hour


settings = Settings()
