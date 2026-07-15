from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.api.dependencies.pagination import PaginationParams
from backend.api.dependencies.uow import get_uow
from backend.core.database.redis import get_redis
from backend.core.uow import IUnitOfWork
from backend.rbac.api.permissions_dependencies import get_current_user
from tests.fixtures.environment_setup import (
    TestUnitOfWork,
    fixture_engine,
    override_get_admin_user,
)


@pytest.fixture(autouse=True)
def mock_audit_task():
    """
    Автоматически отключает отправку задачи AuditLog в RabbitMQ во время тестов.
    """
    # Указываем точный путь импорта до задачи, которую нужно заглушить
    with patch("backend.core.tasks_queue.audit.log_audit_action.kiq", new_callable=AsyncMock) as mock_kiq:
        yield mock_kiq


@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    mock.get.return_value = None
    return mock


@pytest.fixture(scope="function")
async def db_session():
    """
    Создает изолированную сессию для теста.
    Все изменения откатятся после завершения теста.
    """
    async with fixture_engine.connect() as conn:
        # Начинаем корневую транзакцию
        transaction = await conn.begin()

        # Создаем sessionmaker, жестко привязанный к этому соединению.
        # join_transaction_mode="create_savepoint" говорит Алхимии:
        # "Если внутри кода кто-то вызовет session.begin() или session.commit(),
        # не трогай главную транзакцию, а делай SAVEPOINT".
        TestSessionMaker = async_sessionmaker(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )

        async with TestSessionMaker() as session:
            yield session

        # Тест завершен. Жестко откатываем ВСЁ, что наделал тест,
        # возвращая базу к состоянию после prepare_db_and_data
        await transaction.rollback()


@pytest.fixture
async def uow(db_session: AsyncSession) -> TestUnitOfWork:
    """Создает тестовый UoW с реальной тестовой сессией БД"""
    return TestUnitOfWork(session=db_session)


@pytest.fixture
async def client(db_session: AsyncSession, app, mock_redis) -> AsyncGenerator[httpx.AsyncClient, None]:
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
    app.dependency_overrides[get_redis] = lambda: mock_redis

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
