"""
Configuration settings for the Crime Risk API
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Database settings
    DATABASE_URL: str = "postgresql://localhost/crime_risk_db"
    
    # Capital Region (Albany, NY) bounds
    REGION_MIN_LAT: float = 42.5
    REGION_MAX_LAT: float = 42.9
    REGION_MIN_LON: float = -74.1
    REGION_MAX_LON: float = -73.5
    
    # H3 grid resolution (9 = ~0.1 km² cells)
    H3_RESOLUTION: int = 9
    
    # Model settings
    MODEL_VERSION: str = "1.0.0"
    CONFIDENCE_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
