from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import normalize_database_url
from app.database import SessionLocal, engine
from app.main import app
from app.models import Base
from app.seed import seed_data


@pytest.fixture(scope="session", autouse=True)
async def database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_data(session)
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as api:
        yield api


async def login(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()


def test_normalize_external_postgres_urls():
    assert normalize_database_url("postgresql://user:pass@example.com/db").startswith("postgresql+asyncpg://")
    assert (
        normalize_database_url("postgresql://user:pass@example.com/db?sslmode=require")
        == "postgresql+asyncpg://user:pass@example.com/db?ssl=require"
    )
    assert (
        normalize_database_url("postgres://user:pass@example.com/db?sslmode=verify-full")
        == "postgresql+asyncpg://user:pass@example.com/db?ssl=require"
    )


@pytest.mark.asyncio
async def test_health_and_frontend(client):
    health = await client.get("/api/health")
    cache_metrics = await client.get("/api/metrics/cache")
    frontend = await client.get("/")

    assert health.status_code == 200
    assert health.headers["X-CO2-Kg"]
    assert cache_metrics.status_code == 200
    assert "questions" in cache_metrics.json()
    assert "SanteBien" in frontend.text


@pytest.mark.asyncio
async def test_ai_question_analysis_is_frugal_and_non_diagnostic(client):
    response = await client.post(
        "/api/ai/analyze-question",
        json={
            "title": "Comment mieux gérer mon stress au quotidien ?",
            "description": "Je dors mal depuis plusieurs semaines et je cherche des habitudes simples pour réduire mon angoisse.",
            "tags": ["stress"],
            "mode": "int8",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["category"] == "mental"
    assert payload["model"]["mode"] == "int8"
    assert payload["model"]["int8_size_bytes"] < payload["model"]["fp32_size_bytes"]
    assert "aucun diagnostic" in payload["disclaimer"]


@pytest.mark.asyncio
async def test_register_login_and_profile(client):
    email = f"user-{uuid4()}@example.com"
    registered = await client.post(
        "/api/auth/register",
        json={"email": email, "display_name": "Nouveau membre", "password": "Password123!"},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]

    profile = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == email


@pytest.mark.asyncio
async def test_question_comment_and_cache(client):
    session = await login(client, "user@santebien.fr", "User123!")
    headers = {"Authorization": f"Bearer {session['token']}"}
    created = await client.post(
        "/api/questions",
        headers=headers,
        json={
            "title": "Comment construire une routine de prevention simple ?",
            "description": "Je souhaite construire une routine progressive et realiste pour mieux prendre soin de ma sante.",
            "tags": ["prevention", "habitudes"],
        },
    )
    assert created.status_code == 201
    question_id = created.json()["id"]

    first = await client.get(f"/api/questions/{question_id}")
    second = await client.get(f"/api/questions/{question_id}")
    assert first.headers["X-Cache"] == "MISS"
    assert second.headers["X-Cache"] == "HIT"

    comment = await client.post(
        f"/api/questions/{question_id}/comments",
        headers=headers,
        json={"content": "Je commence par une seule habitude pendant une semaine avant d'en ajouter une autre."},
    )
    assert comment.status_code == 201


@pytest.mark.asyncio
async def test_doctor_application_and_admin_approval(client):
    email = f"doctor-{uuid4()}@example.com"
    registered = await client.post(
        "/api/auth/register",
        json={"email": email, "display_name": "Docteur candidat", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {registered.json()['token']}"}
    application = await client.post(
        "/api/doctor-applications",
        headers=headers,
        json={
            "license_number": "RPPS-TEST-2026",
            "specialty": "Dermatologie",
            "document_url": "https://example.org/justificatif.pdf",
            "motivation": "Je souhaite partager des informations de prevention fiables avec la communaute.",
        },
    )
    assert application.status_code == 201

    admin = await login(client, "admin@santebien.fr", "Admin123!")
    approved = await client.patch(
        f"/api/admin/doctor-applications/{application.json()['id']}",
        headers={"Authorization": f"Bearer {admin['token']}"},
        json={"status": "approved", "admin_note": "Justificatifs verifies."},
    )
    assert approved.status_code == 200
    assert approved.json()["user"]["role"] == "doctor"


@pytest.mark.asyncio
async def test_only_doctor_can_publish_article(client):
    user = await login(client, "user@santebien.fr", "User123!")
    response = await client.post(
        "/api/articles",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "title": "Un titre suffisamment long",
            "summary": "Un resume suffisamment long pour etre valide correctement.",
            "content": "A" * 120,
            "tags": ["prevention"],
        },
    )
    assert response.status_code == 403
