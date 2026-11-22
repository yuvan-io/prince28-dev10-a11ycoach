"""Async SQLAlchemy engine and session factory."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from a11ycoach.config import Settings
from a11ycoach.db.url import to_asyncpg_url


def make_engine(settings: Settings):
    """Create an asynchronous PostgreSQL engine."""
    return create_async_engine(
        to_asyncpg_url(settings.database_url),
        pool_pre_ping=True,
    )


def make_sessionmaker(engine):
    """Create a reusable asynchronous session factory."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
