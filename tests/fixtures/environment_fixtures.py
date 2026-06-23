from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies.pagination import PaginationParams
from backend.api.dependencies.permissions import get_current_user
from backend.api.dependencies.uow import get_uow
from backend.core.uow import IUnitOfWork
from tests.fixtures.environment_setup import TestUnitOfWork, fixture_async_session_maker, override_get_admin_user


@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    mock.get.return_value = None
    return mock


@pytest.fixture
async def db_session():
    async with fixture_async_session_maker() as session:
        yield session


@pytest.fixture
async def uow(db_session: AsyncSession) -> TestUnitOfWork:
    """Создает тестовый UoW с реальной тестовой сессией БД"""
    return TestUnitOfWork(session=db_session)


@pytest.fixture
async def client(db_session: AsyncSession, app) -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Создает тестовый HTTP-клиент с подмененными зависимостями:
    - UoW использует тестовую сессию БД
    - get_current_user возвращает админа
    """

    # Создаем фабрику для override_get_uow, которая замыкает db_session
    def override_uow_factory() -> IUnitOfWork:
        return TestUnitOfWork(session=db_session)

    # Подменяем зависимости
    app.dependency_overrides[get_uow] = override_uow_factory
    app.dependency_overrides[get_current_user] = override_get_admin_user

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),  # <-- ИСПОЛЬЗУЙ ЭТО
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_session_factory():
    """Создает мок для сессии и фабрики сессий"""
    session_mock = MagicMock()
    session_mock.close = AsyncMock()
    session_mock.commit = AsyncMock()
    session_mock.rollback = AsyncMock()

    factory_mock = MagicMock()
    factory_mock.return_value = session_mock

    return factory_mock, session_mock


@pytest.fixture
def mock_uow():
    """
    Создаем глобальный мок для Unit of Work.
    Он должен уметь работать в async with и содержать вложенные моки репозиториев.
    """
    uow = AsyncMock()

    # Настраиваем асинхронный контекстный менеджер (async with self.uow)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None

    # Мокаем вложенные репозитории
    uow.users = AsyncMock()
    uow.auth = AsyncMock()
    uow.register = AsyncMock()
    uow.tasks = AsyncMock()
    uow.comments = AsyncMock()
    uow.teams = AsyncMock()
    uow.rbac = AsyncMock()
    uow.evaluations = AsyncMock()

    # Мокаем методы самого UoW
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    return uow


@pytest.fixture
def params():
    return PaginationParams(page=1, size=20)
