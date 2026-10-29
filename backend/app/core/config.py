import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SATYA-APAAR"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AICTE Student Data Management and Verification Platform"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://satya_user:satya_secure_password_2026@localhost:5432/satya_apaar_db"
    SQLITE_FALLBACK: bool = True
    SQLITE_URL: str = "sqlite:///./satya_apaar.db"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Security
    SECRET_KEY: str = "satya_apaar_jwt_super_secret_key_sih2026_demo_key_987654321"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AES-256 Key (must be exactly 32 bytes)
    AES_SECRET_KEY: str = "satya_aes_256_super_key_32bytes_len!"

    # Ed25519 Keys for offline verifiable QR credentials
    ED25519_PRIVATE_KEY_B64: str = ""
    ED25519_PUBLIC_KEY_B64: str = ""

    # AI & Agent
    ANTHROPIC_API_KEY: str = "mock_claude_api_key_or_set_real_key"
    AI_MOCK_FALLBACK: bool = True

    # Policy Thresholds
    SEAT_WARNING_THRESHOLD: float = 0.90  # 90% warn
    SEAT_LOCK_THRESHOLD: float = 1.00     # 100% lock normal admissions

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    @field_validator("CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if v == "*" or not v:
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
