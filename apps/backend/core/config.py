"""
Configuration module for Web+ backend
Handles all environment variables and settings
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Application settings
    app_name: str = "Web+ Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./web_plus.db"
    database_echo: bool = False
    
    # PostgreSQL specific settings (for production)
    postgres_server: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_port: int = 5432
    
    # Security settings
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    cors_allow_headers: List[str] = ["*"]
    cors_expose_headers: List[str] = ["Content-Length", "X-Total-Count"]
    
    # API settings
    api_prefix: str = "/api"
    api_keys: List[str] = []  # Legacy API keys for backward compatibility
    
    # Ollama settings
    ollama_url: str = "http://localhost:11434"
    ollama_timeout: int = 30
    
    # File upload settings
    upload_dir: str = "./uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = [
        ".txt", ".md", ".pdf", ".doc", ".docx",
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".json", ".yaml", ".yml", ".xml",
        ".csv", ".log"
    ]
    
    # WebSocket settings
    ws_heartbeat_interval: int = 30  # seconds
    ws_max_connections: int = 100
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    
    # Redis settings (for future use)
    redis_url: Optional[str] = None
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Monitoring
    enable_metrics: bool = True
    metrics_path: str = "/metrics"
    
    class Config:
        env_file = ".env"
        env_prefix = "WEBPLUS_"
        case_sensitive = False
        
        # Allow extra fields from environment
        extra = "allow"
    
    @validator("database_url", pre=True)
    def construct_db_url(cls, v: Optional[str], values: dict) -> str:
        """Construct database URL from components if not provided directly."""
        if v and v != "sqlite+aiosqlite:///./web_plus.db":
            return v
        
        # Check if PostgreSQL settings are provided
        postgres_server = values.get("postgres_server")
        if postgres_server:
            postgres_user = values.get("postgres_user", "postgres")
            postgres_password = values.get("postgres_password", "")
            postgres_db = values.get("postgres_db", "webplus")
            postgres_port = values.get("postgres_port", 5432)
            
            # Construct PostgreSQL URL
            if postgres_password:
                return f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_server}:{postgres_port}/{postgres_db}"
            else:
                return f"postgresql+asyncpg://{postgres_user}@{postgres_server}:{postgres_port}/{postgres_db}"
        
        # Default to SQLite
        return v or "sqlite+aiosqlite:///./web_plus.db"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return "postgresql" in self.database_url
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return "sqlite" in self.database_url
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return "postgresql" in self.database_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Create a global settings instance
settings = get_settings()