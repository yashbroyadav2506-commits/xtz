import os


def _database_url():
    database_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not database_url:
        if os.environ.get("VERCEL") == "1":
            raise RuntimeError(
                "Set DATABASE_URL to a persistent PostgreSQL connection string in Vercel."
            )
        return "sqlite:///books_swap.db"
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url.removeprefix("postgres://")
    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    return database_url


def _secret_key():
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key and os.environ.get("VERCEL") == "1":
        raise RuntimeError("Set a strong SECRET_KEY environment variable in Vercel.")
    return secret_key or "dev-only-change-me"


class Config:
    SECRET_KEY = _secret_key()
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}
    ITEMS_PER_PAGE = 12
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("VERCEL") == "1"
