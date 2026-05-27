import os
from dotenv import load_dotenv

load_dotenv(override=False)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-k8x9m2")

    # Supabase / PostgreSQL connection string
    # Format: postgresql://user:password@host:port/dbname
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 1800
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
