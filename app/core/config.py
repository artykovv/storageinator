from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "storageinator"

    # S3/MinIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_public_url: str = "http://localhost:9000"  # URL accessible from browser
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "storageinator"
    s3_region: str = "us-east-1"

    # JWT
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # App
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    max_file_size_mb: int = 100
    allowed_mime_types: str = "image/jpeg,image/png,image/gif,application/pdf,text/plain,application/zip,video/mp4,video/webm,video/ogg"
    
    # Admin
    admin_email: str = "admin@example.com"
    admin_password: str = "changeme123"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def allowed_mime_types_list(self) -> List[str]:
        return [mime.strip() for mime in self.allowed_mime_types.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
