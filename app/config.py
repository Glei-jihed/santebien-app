import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgres://")
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgresql://")

    if not url.startswith("postgresql+asyncpg://"):
        return url

    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    sslmode = query.pop("sslmode", None)
    if sslmode and "ssl" not in query:
        query["ssl"] = "require" if sslmode in {"require", "verify-ca", "verify-full"} else sslmode
    if parts.hostname and parts.hostname.endswith(".render.com") and "ssl" not in query:
        query["ssl"] = "require"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


class Settings:
    app_name = "SanteBien"
    database_url = normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./santebien.db",
        )
    )
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    session_days = int(os.getenv("SESSION_DAYS", "14"))
    seed_demo_data = os.getenv("SEED_DEMO_DATA", "true").lower() == "true"
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    admin_display_name = os.getenv("ADMIN_DISPLAY_NAME", "Administrateur SanteBien").strip()


settings = Settings()
