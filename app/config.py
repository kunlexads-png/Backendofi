import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "OFI Cocoa Warehouse AI Assistant"
    API_V1_STR: str = "/api"
    
    # Environment & Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/ofi_cocoa_warehouse"
    )
    
    # Security
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", 
        "ofi_cocoa_warehouse_super_secret_jwt_key_2026_change_in_production"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # Uploads
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [
        "csv", "xlsx", "xls", "pdf", "jpg", "jpeg", "png"
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        return ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
