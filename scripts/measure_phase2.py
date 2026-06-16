import asyncio
import json
import statistics
from pathlib import Path

import httpx
from codecarbon import OfflineEmissionsTracker

from app.main import app

OUTPUT = Path("outputs/phase-2-measures.json")


def percentile(values: list[float], percent: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * percent))
    return ordered[index]


async def measure() -> dict:
    timings: list[float] = []
    co2_headers: list[float] = []

    tracker = OfflineEmissionsTracker(
        country_iso_code="FRA",
        save_to_file=False,
        log_level="error",
        measure_power_secs=1,
    )
    tracker.start()

    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            questions = (await client.get("/api/questions")).json()
            question_id = questions[0]["id"]

            for _ in range(100):
                response = await client.get(f"/api/questions/{question_id}")
                timings.append(float(response.headers["X-Process-Time-Ms"]))
                co2_headers.append(float(response.headers["X-CO2-Kg"]))

            cache_stats = (await client.get("/api/metrics/cache")).json()

    codecarbon_kg = tracker.stop() or 0
    return {
        "requests_measured": len(timings),
        "latency_ms": {
            "min": round(min(timings), 4),
            "mean": round(statistics.mean(timings), 4),
            "p95": round(percentile(timings, 0.95), 4),
            "max": round(max(timings), 4),
        },
        "cache": cache_stats,
        "co2": {
            "duration_estimate_total_kg": sum(co2_headers),
            "codecarbon_campaign_kg": codecarbon_kg,
            "codecarbon_per_request_kg": codecarbon_kg / len(timings),
        },
    }


if __name__ == "__main__":
    result = asyncio.run(measure())
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
