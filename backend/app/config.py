"""
OpenHeart Cyprus - Application Configuration.

Uses pydantic-settings for type-safe environment variable management.
All sensitive values should be provided via environment variables.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # Environment
    # ==========================================================================
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = Field(default=False)
    app_name: str = "OpenHeart Cyprus"
    app_version: str = "0.1.0"

    # ==========================================================================
    # Database
    # ==========================================================================
    database_url: str = Field(
        default="postgresql+asyncpg://openheart:openheart_dev_password@localhost:5432/openheart",
        description="Async database URL for SQLAlchemy",
    )
    database_url_sync: str = Field(
        default="postgresql://openheart:openheart_dev_password@localhost:5432/openheart",
        description="Sync database URL for Alembic migrations",
    )
    db_pool_size: int = Field(default=5, ge=1, le=20)
    db_max_overflow: int = Field(default=10, ge=0, le=50)

    # ==========================================================================
    # Redis
    # ==========================================================================
    redis_url: str = Field(
        default="redis://:openheart_redis_dev@localhost:6379/0",
        description="Redis connection URL",
    )
    redis_session_ttl: int = Field(
        default=3600, description="Session TTL in seconds (1 hour)"
    )

    # ==========================================================================
    # Security
    # ==========================================================================
    secret_key: str = Field(
        default="dev_secret_key_change_in_production_32chars",
        min_length=32,
        description="Secret key for JWT signing",
    )
    pii_encryption_key: str = Field(
        default="dev_encryption_key_32_chars_here!",
        description="Fernet key for PII encryption",
    )
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = Field(default=15, ge=5, le=60)
    refresh_token_expiry_days: int = Field(default=7, ge=1, le=30)

    # MFA Settings
    mfa_required: bool = Field(
        default=True, description="Require MFA for all clinical accounts"
    )
    totp_issuer: str = "OpenHeart Cyprus"

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Requests per window")
    rate_limit_window_seconds: int = Field(default=60, description="Window in seconds")

    # ==========================================================================
    # CORS
    # ==========================================================================
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )

    # ==========================================================================
    # Orthanc (DICOM Server)
    # ==========================================================================
    orthanc_url: str = Field(
        default="http://localhost:8042", description="Orthanc server URL"
    )
    orthanc_username: str = Field(default="admin")
    orthanc_password: str = Field(default="orthanc_dev_password")

    # ==========================================================================
    # S3/MinIO (File Storage)
    # ==========================================================================
    s3_endpoint: str = Field(
        default="http://localhost:9000", description="S3/MinIO endpoint"
    )
    s3_access_key: str = Field(default="openheart_minio")
    s3_secret_key: str = Field(default="openheart_minio_dev")
    s3_bucket: str = Field(default="openheart-attachments")
    s3_region: str = Field(default="us-east-1")

    # ==========================================================================
    # Gesy Integration (Optional)
    # ==========================================================================
    gesy_api_url: str | None = Field(default=None, description="Gesy API URL")
    gesy_api_key: str | None = Field(default=None, description="Gesy API key")
    gesy_provider_id: str | None = Field(default=None, description="HIO Provider ID")

    # ==========================================================================
    # OpenAI (Optional - for semantic search)
    # ==========================================================================
    openai_api_key: str | None = Field(
        default=None, description="OpenAI API key for embeddings"
    )
    embedding_model: str = Field(default="text-embedding-3-small")

    # ==========================================================================
    # File Upload
    # ==========================================================================
    max_upload_size_mb: int = Field(default=50, ge=1, le=100)
    allowed_file_types: list[str] = Field(
        default=["application/pdf", "application/msword",
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                 "image/jpeg", "image/png", "text/plain"]
    )

    # ==========================================================================
    # Computed Properties
    # ==========================================================================
    @computed_field  # type: ignore[misc]
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @computed_field  # type: ignore[misc]
    @property
    def base_url(self) -> str:
        """Get base URL based on environment."""
        if self.is_production:
            return "https://api.openheart.cy"
        return "http://localhost:8000"

    @computed_field  # type: ignore[misc]
    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export singleton
settings = get_settings()
