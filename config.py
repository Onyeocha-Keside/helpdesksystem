import os
from typing import List
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4"
    
    # Application Configuration
    app_name: str = "Intelligent Help Desk System"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # API Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Vector Search Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.7
    
    # Data Paths
    data_dir: str = "data"
    
    # Hardcoded escalation categories (simpler approach)
    @property
    def auto_escalate_categories(self) -> List[str]:
        return ["security_incident", "hardware_failure"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings