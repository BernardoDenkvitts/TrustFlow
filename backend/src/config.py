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

    # Database
    database_url: str = "postgresql+asyncpg://trustflow:trustflow@localhost:5432/trustflow"

    # Blockchain
    rpc_url: str = "http://localhost:8545"
    chain_id: int = 31337  # Anvil default
    escrow_contract_address: str = ""

    # Sync Worker
    sync_interval_seconds: int = 15
    confirmations: int = 2


settings = Settings()
