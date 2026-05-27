import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-k8x9m2")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "bank_management")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 1800
    SESSION_COOKIE_HTTPONLY = True  # Prevents client-side scripts from reading session cookies (XSS protection)
    SESSION_COOKIE_SAMESITE = "Lax"  # Blocks CSRF (Cross-Site Request Forgery) attacks on session cookies
