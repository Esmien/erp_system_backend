import pytest
from httpx import AsyncClient, ASGITransport

from backend.api.main import app


@pytest.fixture
async def client():

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
        await ac.aclose()
