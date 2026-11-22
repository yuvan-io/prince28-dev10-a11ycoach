"""Check that the Neon PostgreSQL database is reachable."""

import asyncio

from sqlalchemy import text

from a11ycoach.config import get_settings
from a11ycoach.db.session import make_engine


async def main() -> None:
    settings = get_settings()
    engine = make_engine(settings)

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT current_database(), version()"))
            database_name, postgres_version = result.one()

            print(f"Connected to database '{database_name}'")
            print(postgres_version)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
