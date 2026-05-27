import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-k8x9m2")
    MYSQL_HOST = os.getenv("MYSQL_HOST") or os.getenv("MYSQLHOST") or os.getenv("DB_HOST") or "localhost"
    MYSQL_USER = os.getenv("MYSQL_USER") or os.getenv("MYSQLUSER") or os.getenv("DB_USER") or "root"
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD") or os.getenv("MYSQLPASSWORD") or os.getenv("DB_PASSWORD") or ""
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE") or os.getenv("MYSQLDATABASE") or os.getenv("DB_NAME") or "bank_management"
    MYSQL_PORT = int(os.getenv("MYSQL_PORT") or os.getenv("MYSQLPORT") or os.getenv("DB_PORT") or 3306)
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 1800
    SESSION_COOKIE_HTTPONLY = True  # Prevents client-side scripts from reading session cookies (XSS protection)
    SESSION_COOKIE_SAMESITE = "Lax"  # Blocks CSRF (Cross-Site Request Forgery) attacks on session cookies
