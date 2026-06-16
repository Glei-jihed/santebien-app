import os


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    return url


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


settings = Settings()
