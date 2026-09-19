import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    test_engine = create_async_engine(
        settings.database_url,
        echo=True,
        poolclass=NullPool,
    )

    test_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with test_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()

    await test_engine.dispose()