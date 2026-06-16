import asyncio

from app.database import SessionLocal, engine
from app.models import Base
from app.seed import seed_data


async def reset_demo() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        await seed_data(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_demo())
    print("Base de demonstration SanteBien reinitialisee.")
