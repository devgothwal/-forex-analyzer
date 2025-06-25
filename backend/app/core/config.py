"""
Configuration Management - Environment-based settings with validation
Supports development, staging, and production environments
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Info
    APP_NAME: str = "Forex Trading Analysis Platform"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Modular platform for analyzing forex trading data"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "https://localhost:3000"
    ]
    
    # Database
    DATABASE_URL: str = "sqlite:///./forex_analyzer.db"
    DATABASE_ECHO: bool = False
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]
    
    # ML Pipeline
    ML_MODEL_DIR: str = "models"
    ML_CACHE_DIR: str = "cache"
    ML_MAX_TRAINING_TIME: int = 300  # 5 minutes
    
    # Plugin System
    PLUGIN_DIRS: List[str] = ["plugins", "../plugins"]
    PLUGIN_TIMEOUT: int = 30
    PLUGIN_MAX_MEMORY: int = 512 * 1024 * 1024  # 512MB
    
    # Event System
    EVENT_HISTORY_SIZE: int = 1000
    EVENT_BATCH_SIZE: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance
    ENABLE_CACHING: bool = True
    CACHE_TTL: int = 3600  # 1 hour
    MAX_CONCURRENT_ANALYSES: int = 5
    
    # Features Flags
    ENABLE_REAL_TIME_ANALYSIS: bool = False
    ENABLE_ADVANCED_ML: bool = True
    ENABLE_PLUGIN_MARKETPLACE: bool = False
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("ENVIRONMENT must be one of: development, staging, production")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v.upper()
    
    @validator("ALLOWED_ORIGINS")
    def validate_origins(cls, v):
        # In production, ensure we don't allow all origins
        if "*" in v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("Wildcard origins not allowed in production")
        return v
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for non-async operations"""
        if self.DATABASE_URL.startswith("sqlite"):
            return self.DATABASE_URL
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    def get_upload_path(self) -> Path:
        """Get the upload directory path"""
        path = Path(self.UPLOAD_DIR)
        path.mkdir(exist_ok=True)
        return path
    
    def get_model_path(self) -> Path:
        """Get the ML model directory path"""
        path = Path(self.ML_MODEL_DIR)
        path.mkdir(exist_ok=True)
        return path
    
    def get_cache_path(self) -> Path:
        """Get the cache directory path"""
        path = Path(self.ML_CACHE_DIR)
        path.mkdir(exist_ok=True)
        return path
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DATABASE_ECHO: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENABLE_REAL_TIME_ANALYSIS: bool = True


class ProductionSettings(Settings):
    """Production environment settings"""
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    DATABASE_ECHO: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: List[str] = []  # Must be configured via environment


class TestingSettings(Settings):
    """Testing environment settings"""
    ENVIRONMENT: str = "testing"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./test.db"
    LOG_LEVEL: str = "WARNING"


def get_settings() -> Settings:
    """Factory function to get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()


# Plugin Configuration Schema
PLUGIN_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "enabled": {"type": "boolean", "default": True},
        "config": {
            "type": "object",
            "properties": {
                "timeout": {"type": "integer", "default": 30},
                "max_memory": {"type": "integer", "default": 100 * 1024 * 1024},
                "cache_results": {"type": "boolean", "default": True},
                "log_level": {"type": "string", "default": "INFO"}
            }
        },
        "dependencies": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}


# ML Model Configuration Schema
ML_MODEL_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "enabled_models": {
            "type": "array",
            "items": {"type": "string"},
            "default": ["random_forest", "decision_tree", "kmeans"]
        },
        "hyperparameters": {
            "type": "object",
            "default": {}
        },
        "cross_validation": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "folds": {"type": "integer", "default": 5},
                "scoring": {"type": "string", "default": "accuracy"}
            }
        },
        "feature_selection": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": True},
                "method": {"type": "string", "default": "mutual_info"},
                "max_features": {"type": "integer", "default": 20}
            }
        }
    }
}