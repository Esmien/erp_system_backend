from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from backend.rbac.repository import RbacRepository
from backend.rbac.service import RbacService
from backend.team.repository import TeamRepository
from backend.team.service import TeamService
from backend.user.repository import RegisterRepository, AuthRepository, UserRepository
from backend.user.service import RegisterService, AuthService, UserService
from tests.fixtures.environment_setup import fixture_async_session_maker


@pytest_asyncio.fixture
async def db_session():
    async with fixture_async_session_maker() as session:
        yield session


@pytest.fixture
def mock_session_factory():
    """Создает мок для сессии и фабрики сессий"""
    session_mock = AsyncMock()
    factory_mock = MagicMock(return_value=session_mock)
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
    uow.teams = AsyncMock()

    # Мокаем методы самого UoW
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    return uow


@pytest.fixture
def rbac_service(mock_uow):
    return RbacService(uow=mock_uow)


@pytest.fixture
def team_service(mock_uow):
    return TeamService(uow=mock_uow)


@pytest.fixture
def register_service(mock_uow):
    return RegisterService(uow=mock_uow)


@pytest.fixture
def auth_service(mock_uow):
    return AuthService(uow=mock_uow)


@pytest.fixture
def user_service(mock_uow):
    return UserService(uow=mock_uow)


@pytest.fixture
def rbac_repo(db_session):
    return RbacRepository(session=db_session)


@pytest.fixture
def team_repo(db_session):
    return TeamRepository(session=db_session)


@pytest.fixture
def register_repo(db_session):
    return RegisterRepository(session=db_session)


@pytest.fixture
def auth_repo(db_session):
    return AuthRepository(session=db_session)


@pytest.fixture
def user_repo(db_session):
    return UserRepository(session=db_session)
