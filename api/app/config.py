import os


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "postgresql://cockpit:cockpit@localhost:5432/cockpit")
    # O Railway entrega postgresql://; o SQLAlchemy com psycopg 3 precisa do driver explícito.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)
