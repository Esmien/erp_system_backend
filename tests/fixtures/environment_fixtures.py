from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from backend.api.dependencies.pagination import PaginationParams
from tests.fixtures.environment_setup import fixture_async_session_maker


@pytest_asyncio.fixture
async def db_session():
    async with fixture_async_session_maker() as session:
        yield session


@pytest.fixture
def mock_session_factory():
    """Создает мок для сессии и фабрики сессий"""
    session_mock = MagicMock()
    session_mock.close = AsyncMock()
    session_mock.commit = AsyncMock()
    session_mock.rollback = AsyncMock()

    factory_mock = MagicMock()
    factory_mock.return_value.__aenter__ = AsyncMock(return_value=session_mock)
    factory_mock.return_value.__aexit__ = AsyncMock(return_value=False)

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
