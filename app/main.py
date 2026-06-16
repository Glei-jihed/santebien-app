from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select

from app.cache import Cache
from app.config import settings
from app.database import SessionLocal, engine
from app.models import Article, Base, Question, User
from app.routers import admin, articles, auth, doctors, questions
from app.seed import seed_data, seed_initial_admin

ESTIMATED_SERVER_WATTS = 35
FRANCE_KG_CO2_PER_KWH = 0.052
STATIC_DIR = Path(__file__).parent / "static"
cache = Cache()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await cache.connect()
    await questions.cache.connect()
    await articles.cache.connect()
    if settings.seed_demo_data:
        async with SessionLocal() as db:
            await seed_data(db)
    if settings.admin_email and settings.admin_password:
        async with SessionLocal() as db:
            await seed_initial_admin(
                db,
                settings.admin_email,
                settings.admin_password,
                settings.admin_display_name,
            )
    yield
    await engine.dispose()


app = FastAPI(
    title="SanteBien API",
    version="1.0.0",
    description="Plateforme communautaire de sante sobre et moderee.",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_measurement_headers(request: Request, call_next):
    started = perf_counter()
    response: Response = await call_next(request)
    duration_seconds = perf_counter() - started
    energy_kwh = ESTIMATED_SERVER_WATTS * duration_seconds / 3_600_000
    response.headers["X-Process-Time-Ms"] = f"{duration_seconds * 1_000:.3f}"
    response.headers["X-CO2-Kg"] = f"{energy_kwh * FRANCE_KG_CO2_PER_KWH:.12f}"
    response.headers["X-Cache-Backend"] = cache.backend
    return response


api_prefix = "/api"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(questions.router, prefix=api_prefix)
app.include_router(articles.router, prefix=api_prefix)
app.include_router(doctors.router, prefix=api_prefix)
app.include_router(admin.router, prefix=api_prefix)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "database": settings.database_url.split(":", 1)[0], "cache": cache.backend}


@app.get("/api/stats")
async def stats() -> dict:
    async with SessionLocal() as db:
        return {
            "members": await db.scalar(select(func.count(User.id))),
            "questions": await db.scalar(select(func.count(Question.id))),
            "articles": await db.scalar(select(func.count(Article.id))),
            "verified_doctors": await db.scalar(select(func.count(User.id)).where(User.role == "doctor")),
        }


@app.get("/api/metrics/cache")
async def cache_metrics() -> dict:
    return {
        "application": cache.stats(),
        "questions": questions.cache.stats(),
        "articles": articles.cache.stats(),
    }


app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/{path:path}", include_in_schema=False)
async def frontend(path: str) -> FileResponse:
    del path
    return FileResponse(STATIC_DIR / "index.html")
