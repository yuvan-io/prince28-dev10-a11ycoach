"""Run integration tests against a fresh, temporary PostgreSQL database."""

import asyncio
import os
import subprocess
import sys
import uuid

import asyncpg

ADMIN_URL = "postgresql://postgres:postgres@localhost:5432/postgres"


async def create_database(name: str) -> None:
    conn = await asyncpg.connect(ADMIN_URL)
    try:
        await conn.execute(f'CREATE DATABASE "{name}"')
    finally:
        await conn.close()


async def drop_database(name: str) -> None:
    conn = await asyncpg.connect(ADMIN_URL)
    try:
        await conn.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = $1 AND pid <> pg_backend_pid()
            """,
            name,
        )
        await conn.execute(f'DROP DATABASE IF EXISTS "{name}"')
    finally:
        await conn.close()


def main() -> int:
    name = f"a11ycoach_test_{uuid.uuid4().hex[:12]}"
    database_url = f"postgresql://postgres:postgres@localhost:5432/{name}"

    print(f"Creating fresh database: {name}")
    asyncio.run(create_database(name))

    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["APP_ENV"] = "ci"

    try:
        print("Applying migrations...")
        migration = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=env,
            check=False,
        )
        if migration.returncode:
            return migration.returncode

        print("Running integration tests...")
        tests = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/integration",
                "--cov=a11ycoach",
                "--cov-report=term-missing",
            ],
            env=env,
            check=False,
        )
        return tests.returncode
    finally:
        print(f"Removing temporary database: {name}")
        asyncio.run(drop_database(name))


if __name__ == "__main__":
    raise SystemExit(main())
