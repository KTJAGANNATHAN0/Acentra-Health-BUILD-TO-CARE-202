"""Accentra Fraud Engine Application Configuration."""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Accentra Fraud Rule Engine"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./fraud_engine.db"
    
    # Thresholds
    FLAG_THRESHOLD: int = 50       # Score >= 50 marks transaction as flagged (PENDING)
    HIGH_RISK_THRESHOLD: int = 80  # Score >= 80 triggers SNS/SES alert
    
    # Notifications (sns | ses | log)
    NOTIFIER: str = "log"
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    SNS_TOPIC_ARN: Optional[str] = None
    SES_SENDER: Optional[str] = "alerts@fraud-engine.internal"
    SES_RECIPIENTS: List[str] = ["security-team@fraud-engine.internal"]
    
    # Reviewer Console URL (used in alert links)
    CONSOLE_URL: str = "http://localhost:5173"
    
    # API Security
    API_KEY_ENABLED: bool = False
    API_KEY: str = "dev-secret-key-accentra"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
