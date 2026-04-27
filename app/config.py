from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Deeps Systems OpsCentre"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./opscentre.db"

    # JWT
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_USE_256BIT_RANDOM"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8h shift coverage

    # MinIO (local S3-compatible storage)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "opscentre-media"
    minio_secure: bool = False

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
