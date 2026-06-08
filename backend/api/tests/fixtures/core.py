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


@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    """
    Автоматически делает бэкап и восстанавливает app.dependency_overrides
    для КАЖДОГО теста. Больше никаких утечек состояния!
    """
    # Сохраняем текущее состояние моков (например, твой базовый мок авторизации)
    original_overrides = app.dependency_overrides.copy()

    yield  # Тут выполняется тест

    # Жестко возвращаем всё как было
    app.dependency_overrides = original_overrides
