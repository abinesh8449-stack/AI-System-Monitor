import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    """Application configuration loaded from environment with robust defaults."""
    
    # Flask Security & Session
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-secret-key-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Server Binding
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("FLASK_ENV", "production").lower() == "development"
    
    # Database Settings
    DATABASE_PATH = BASE_DIR / "data" / "monitoring.db"
    
    # Timing Intervals (Seconds)
    REALTIME_UPDATE_INTERVAL = float(os.getenv("REALTIME_UPDATE_INTERVAL", 1.5))
    PERSISTENCE_INTERVAL = float(os.getenv("PERSISTENCE_INTERVAL", 5.0))
    ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", 300))
    
    # Centralized Resource Thresholds (Percentages)
    # CPU: 0-49% HEALTHY, 50-80% WARNING, >80% CRITICAL
    CPU_WARNING = float(os.getenv("CPU_WARNING_THRESHOLD", 50.0))
    CPU_CRITICAL = float(os.getenv("CPU_CRITICAL_THRESHOLD", 80.0))
    
    # RAM: 0-49% HEALTHY, 50-80% WARNING, >80% CRITICAL
    RAM_WARNING = float(os.getenv("RAM_WARNING_THRESHOLD", 50.0))
    RAM_CRITICAL = float(os.getenv("RAM_CRITICAL_THRESHOLD", 80.0))
    
    # Disk: 0-69% HEALTHY, 70-85% WARNING, >85% CRITICAL
    DISK_WARNING = float(os.getenv("DISK_WARNING_THRESHOLD", 70.0))
    DISK_CRITICAL = float(os.getenv("DISK_CRITICAL_THRESHOLD", 85.0))
    
    # Network status evaluation
    NETWORK_PING_HOST = os.getenv("NETWORK_PING_HOST", "8.8.8.8")
    NETWORK_PING_PORT = int(os.getenv("NETWORK_PING_PORT", 53))
    NETWORK_TIMEOUT = float(os.getenv("NETWORK_TIMEOUT", 1.5))
    
    # Email SMTP Settings
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() in ("true", "1", "yes")
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT", "")
    
    # Default Admin Credentials for Seed
    DEFAULT_ADMIN_USER = os.getenv("DEFAULT_ADMIN_USER", "admin")
    DEFAULT_ADMIN_PASS = os.getenv("DEFAULT_ADMIN_PASS", "Admin@123")
