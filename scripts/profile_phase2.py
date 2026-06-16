import asyncio
import cProfile
import io
import pstats
from pathlib import Path

import httpx

from app.main import app

PROFILE_PATH = Path("outputs/phase-2-profile.prof")
REPORT_PATH = Path("outputs/phase-2-profile.txt")


async def exercise_api() -> None:
    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            questions = (await client.get("/api/questions")).json()
            question_id = questions[0]["id"]

            for _ in range(1_000):
                await client.get(f"/api/questions/{question_id}")


def main() -> None:
    PROFILE_PATH.parent.mkdir(exist_ok=True)
    profiler = cProfile.Profile()
    profiler.enable()
    asyncio.run(exercise_api())
    profiler.disable()
    profiler.dump_stats(PROFILE_PATH)

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats("cumulative")
    stats.print_stats(25)
    REPORT_PATH.write_text(stream.getvalue(), encoding="utf-8")
    print(stream.getvalue())


if __name__ == "__main__":
    main()
