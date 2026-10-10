import pytest

from config import _database_url, _secret_key


@pytest.mark.parametrize(
    ("raw_url", "expected"),
    [
        ("postgres://user:pass@host/db", "postgresql+psycopg://user:pass@host/db"),
        ("postgresql://user:pass@host/db", "postgresql+psycopg://user:pass@host/db"),
        (
            "postgresql+psycopg://user:pass@host/db",
            "postgresql+psycopg://user:pass@host/db",
        ),
    ],
)
def test_postgresql_database_urls_use_psycopg(monkeypatch, raw_url, expected):
    monkeypatch.setenv("DATABASE_URL", raw_url)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    assert _database_url() == expected


def test_vercel_requires_persistent_database(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    with pytest.raises(RuntimeError, match="persistent PostgreSQL"):
        _database_url()


def test_vercel_requires_private_secret_key(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        _secret_key()


def test_local_development_keeps_sqlite_default(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    assert _database_url() == "sqlite:///books_swap.db"


def test_public_stylesheet_is_served_from_vercel_public_folder(client):
    response = client.get("/style.css")
    assert response.status_code == 200
    assert b".book-card" in response.data
