import pytest_asyncio

from tests.fixtures.environment_setup import fixture_async_session_maker


@pytest_asyncio.fixture
async def db_session():
    async with fixture_async_session_maker() as session:
        yield session