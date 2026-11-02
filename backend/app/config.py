import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "SmartSub - Fantasy Cricket Substitution Intelligence"
    APP_VERSION: str = "2.2.0"
    DEBUG: bool = True
    
    # Dual-adapter database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./smartsub_tactical.db")
    SYNC_DATABASE_URL: str = os.getenv("SYNC_DATABASE_URL", "sqlite:///./smartsub_tactical.db")
    
    # Gemini API configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Platform / Simulation Defaults
    DEFAULT_CREDIT_CAP: float = 100.0
    DATA_PROVENANCE_TAG: str = "ILLUSTRATIVE_SIMULATION"
    IS_INDEPENDENTLY_VERIFIED: bool = False

settings = Settings()
