# settings.py
import os
from typing import Optional

class Settings:
    def __init__(self):
        # Schema version
        self.SCHEMA_VERSION = "1.0.0"
        
        # API Keys (from environment or defaults)
        self.ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "OHYSFF1AE446O7CR")
        self.ALPHA_RPS = int(os.getenv("ALPHA_RPS", "5"))  # Alpha Vantage requests per second limit
        self.FINNHUB_KEY = os.getenv("FINNHUB_API_KEY", "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0")
        self.FINNHUB_RPS = int(os.getenv("FINNHUB_RPS", "60"))  # Finnhub requests per second limit
        self.NEWS_API_KEY = os.getenv("NEWS_API_KEY", "94a335c7316145f79840edd62f77e11e")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "REDACTED")
        
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./richesreach.db")
        
        # Redis
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://process.env.REDIS_HOST || "localhost:6379"/0")
        
        # Environment
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"
        
        # CORS
        self.CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
        
        # Security
        self.SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
        
        # API Configuration
        self.API_HOST = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT = int(os.getenv("API_PORT", "8000"))
        
        # Feature Flags
        self.USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"
        self.ENABLE_ML_SERVICES = os.getenv("ENABLE_ML_SERVICES", "true").lower() == "true"
        self.ENABLE_MONITORING = os.getenv("ENABLE_MONITORING", "true").lower() == "true"
        
        # Retry and Backoff Settings
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
        self.BACKOFF_BASE_S = float(os.getenv("BACKOFF_BASE_S", "1.0"))
        
        # Additional API Settings
        self.POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
        self.WALLETCONNECT_PROJECT_ID = os.getenv("WALLETCONNECT_PROJECT_ID", "")
        self.ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY", "")
        self.ALCHEMY_SEPOLIA_URL = os.getenv("ALCHEMY_SEPOLIA_URL", "")
        
        # Test Settings
        self.TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@example.com")
        self.TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "testpassword")
        
        # Production Settings
        self.PRODUCTION_URL = os.getenv("PRODUCTION_URL", "")
        self.SEPOLIA_ETH_RPC_URL = os.getenv("SEPOLIA_ETH_RPC_URL", "")
        
        # SBLOC Settings
        self.USE_SBLOC_MOCK = os.getenv("USE_SBLOC_MOCK", "true").lower() == "true"
        self.USE_YODLEE = os.getenv("USE_YODLEE", "false").lower() == "true"
        self.USE_SBLOC_AGGREGATOR = os.getenv("USE_SBLOC_AGGREGATOR", "false").lower() == "true"
        
        # AWS Settings
        self.AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
        
        # CORS Origins
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Security Headers
        self.SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "false").lower() == "true"
        self.SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
        self.SECURE_CONTENT_TYPE_NOSNIFF = os.getenv("SECURE_CONTENT_TYPE_NOSNIFF", "true").lower() == "true"
        self.SECURE_BROWSER_XSS_FILTER = os.getenv("SECURE_BROWSER_XSS_FILTER", "true").lower() == "true"
        self.X_FRAME_OPTIONS = os.getenv("X_FRAME_OPTIONS", "DENY")
        
        # OpenAI Settings
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        self.OPENAI_TIMEOUT_MS = int(os.getenv("OPENAI_TIMEOUT_MS", "30000"))
        self.OPENAI_ENABLE_FALLBACK = os.getenv("OPENAI_ENABLE_FALLBACK", "true").lower() == "true"

# Global settings instance
settings = Settings()
