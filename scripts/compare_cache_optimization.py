import asyncio
import json
import statistics
from pathlib import Path

import httpx

from app.database import SessionLocal, engine
from app.main import app
from app.models import Base
from app.routers import questions as questions_router
from app.seed import seed_data

OUTPUT = Path("outputs/cache-optimization-comparison.json")


def percentile(values: list[float], percent: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * percent))
    return ordered[index]


def summarize(values: list[float]) -> dict:
    return {
        "min_ms": round(min(values), 4),
        "mean_ms": round(statistics.mean(values), 4),
        "p95_ms": round(percentile(values, 0.95), 4),
        "max_ms": round(max(values), 4),
    }


async def compare() -> dict:
    cold: list[float] = []
    cold_co2: list[float] = []
    warm: list[float] = []
    warm_co2: list[float] = []
    hits = 0
    misses = 0

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_data(session)
    await questions_router.cache.delete_pattern("santebien:questions:*")
    await questions_router.cache.delete_pattern("santebien:question:*")

    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            question_id = (await client.get("/api/questions")).json()[0]["id"]

            for _ in range(100):
                await questions_router.cache.delete_pattern(f"santebien:question:{question_id}*")
                response = await client.get(f"/api/questions/{question_id}")
                cold.append(float(response.headers["X-Process-Time-Ms"]))
                cold_co2.append(float(response.headers["X-CO2-Kg"]))

            await questions_router.cache.delete_pattern(f"santebien:question:{question_id}*")
            await client.get(f"/api/questions/{question_id}")

            for _ in range(100):
                response = await client.get(f"/api/questions/{question_id}")
                warm.append(float(response.headers["X-Process-Time-Ms"]))
                warm_co2.append(float(response.headers["X-CO2-Kg"]))
                if response.headers.get("X-Cache") == "HIT":
                    hits += 1
                else:
                    misses += 1

    cold_summary = summarize(cold)
    warm_summary = summarize(warm)
    cold_total_co2 = sum(cold_co2)
    warm_total_co2 = sum(warm_co2)

    return {
        "scenario": "100 lectures froides vs 100 lectures chaudes avec cache",
        "cold_without_cache_benefit": {
            "requests": len(cold),
            **cold_summary,
            "co2_kg": cold_total_co2,
        },
        "warm_optimized_cache": {
            "requests": len(warm),
            **warm_summary,
            "co2_kg": warm_total_co2,
            "hits": hits,
            "misses": misses,
            "hit_rate_percent": round(hits / len(warm) * 100, 2),
        },
        "gain": {
            "mean_latency_reduction_percent": round(
                (1 - warm_summary["mean_ms"] / cold_summary["mean_ms"]) * 100,
                2,
            ),
            "p95_latency_reduction_percent": round(
                (1 - warm_summary["p95_ms"] / cold_summary["p95_ms"]) * 100,
                2,
            ),
            "co2_reduction_percent": round((1 - warm_total_co2 / cold_total_co2) * 100, 2),
        },
    }


if __name__ == "__main__":
    result = asyncio.run(compare())
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
