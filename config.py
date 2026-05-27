import os

# Only load .env in local development.
# In production (Railway / Render), environment variables are injected
# directly by the platform — we must NOT let a stale .env override them.
_is_production = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER") or os.getenv("PORT")

if not _is_production:
    from dotenv import load_dotenv
    load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-k8x9m2")

    # Priority: platform vars (MYSQLHOST / MYSQLUSER …) → MYSQL_* → localhost fallback
    MYSQL_HOST = (
        os.getenv("MYSQLHOST") or
        os.getenv("MYSQL_HOST") or
        os.getenv("DB_HOST") or
        "localhost"
    )
    MYSQL_USER = (
        os.getenv("MYSQLUSER") or
        os.getenv("MYSQL_USER") or
        os.getenv("DB_USER") or
        "root"
    )
    MYSQL_PASSWORD = (
        os.getenv("MYSQLPASSWORD") or
        os.getenv("MYSQL_PASSWORD") or
        os.getenv("DB_PASSWORD") or
        ""
    )
    MYSQL_DATABASE = (
        os.getenv("MYSQLDATABASE") or
        os.getenv("MYSQL_DATABASE") or
        os.getenv("DB_NAME") or
        "bank_management"
    )
    MYSQL_PORT = int(
        os.getenv("MYSQLPORT") or
        os.getenv("MYSQL_PORT") or
        os.getenv("DB_PORT") or
        3306
    )
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 1800
    SESSION_COOKIE_HTTPONLY = True   # Prevents XSS reading session cookies
    SESSION_COOKIE_SAMESITE = "Lax"  # Blocks CSRF attacks on session cookies
