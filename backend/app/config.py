import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "AI Career Agent"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-career-agent-token-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./career_agent.db")
    
    # Uploads
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    
    # Matching Engine Formula Weights (Configurable as per PRD Section 21)
    WEIGHT_SKILL: float = 0.30
    WEIGHT_SEMANTIC: float = 0.25
    WEIGHT_EXPERIENCE: float = 0.15
    WEIGHT_PREFERENCE: float = 0.15
    WEIGHT_ROLE: float = 0.10
    WEIGHT_EDUCATION: float = 0.05
    
    # Scoring Thresholds (PRD Section 27)
    HIGH_PRIORITY_THRESHOLD: float = 75.0
    CONSIDER_THRESHOLD: float = 55.0

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
