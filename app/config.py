from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./lumina.db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Mock settings - Use mock service to bypass Bakong API
    USE_MOCK_BAKONG: bool = os.getenv("USE_MOCK_BAKONG", "true").lower() == "true"
    
    # CORS - Support both development and production
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        origins = [
            # Development
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://localhost:3002",
            "http://localhost:3003",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
            "http://127.0.0.1:3003",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
        ]
        
        # Add production URLs if in production
        if self.ENVIRONMENT == "production":
            origins.extend([
                "https://frontend-admin-edad.vercel.app",
                "https://front-user-steel.vercel.app",
            ])
        
        # Always allow the current Render domain
        render_domain = os.getenv("RENDER_EXTERNAL_URL")
        if render_domain:
            origins.append(render_domain)
        
        return origins
    
    # File upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp"]
    
    # Stripe (optional)
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Email (optional)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Bakong KHQR Settings - Your credentials
    BAKONG_TOKEN: str = os.getenv("BAKONG_TOKEN", "")
    BAKONG_MERCHANT_ID: str = os.getenv("BAKONG_MERCHANT_ID", "ret_naphut@bkrt")
    BAKONG_PHONE_NUMBER: str = os.getenv("BAKONG_PHONE_NUMBER", "+855972021149")
    BAKONG_EXPIRE_DATE: str = os.getenv("BAKONG_EXPIRE_DATE", "")
    
    @property
    def is_bakong_configured(self) -> bool:
        """Check if Bakong is properly configured"""
        return bool(self.BAKONG_TOKEN and self.BAKONG_MERCHANT_ID)
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()