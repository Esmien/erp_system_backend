import pytest
from httpx import AsyncClient, ASGITransport

from backend.api.dependencies.redis import get_redis
from backend.api.main import app as main_app


@pytest.fixture
def app(mock_redis):
    """Фикстура приложения с переопределенными зависимостями."""
    # Переопределяем провайдер Redis на возврат нашего мока
    main_app.dependency_overrides[get_redis] = lambda: mock_redis

    yield main_app

    # Очищаем переопределения после теста
    main_app.dependency_overrides.pop(get_redis, None)


@pytest.fixture
async def client(app):

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
        await ac.aclose()


@pytest.fixture(autouse=True)
def reset_dependency_overrides(app):
    """
    Автоматически делает бэкап и восстанавливает app.dependency_overrides
    для КАЖДОГО теста. Больше никаких утечек состояния!
    """
    # Сохраняем текущее состояние моков (например, твой базовый мок авторизации)
    original_overrides = app.dependency_overrides.copy()

    yield  # Тут выполняется тест

    # Жестко возвращаем всё как было
    app.dependency_overrides = original_overrides
