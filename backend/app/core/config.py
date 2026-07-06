from dotenv import load_dotenv
import os

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# JWT & Security
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# External Services
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
OCR_API_KEY = os.getenv("OCR_API_KEY", "")

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# CORS & Frontend
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,https://vikas-seed-store.vercel.app").split(",")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://vikas-seed-store.vercel.app" if ENVIRONMENT == "production" else "http://localhost:5173")
API_URL = os.getenv("API_URL", "http://localhost:8000")

# File Uploads
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(52428800)))  # 50MB default
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "app/uploads")
ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif,pdf,doc,docx").split(","))

# Rate Limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

# Logging
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_FILE_MAX_SIZE = int(os.getenv("LOG_FILE_MAX_SIZE", str(10485760)))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "10"))
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json or text

# Security Headers
ENABLE_HSTS = os.getenv("ENABLE_HSTS", "true").lower() == "true"
HSTS_MAX_AGE = int(os.getenv("HSTS_MAX_AGE", "31536000"))
ENABLE_CSP = os.getenv("ENABLE_CSP", "true").lower() == "true"
ENABLE_CSRF_PROTECTION = os.getenv("ENABLE_CSRF_PROTECTION", "true").lower() == "true"

# Monitoring
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))