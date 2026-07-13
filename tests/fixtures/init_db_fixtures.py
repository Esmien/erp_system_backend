import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.core.database.engine import Base
from backend.core.database.init_db import init_basic_data
from backend.core.enums import TaskStatus
from backend.core.security import get_password_hash
from backend.task.models import Task
from backend.team.models import Team
from tests.fixtures.environment_setup import (
    fixture_engine,
)

TEAM_NAME = "Dummy name"
TEAM_CODE = "111111"

_PASSWORDS_CACHE: dict[str, str] = {}


async def _get_cached_password_hash(password: str) -> str:
    """Возвращает закешированный хеш или генерирует новый, если его еще нет"""
    if password not in _PASSWORDS_CACHE:
        _PASSWORDS_CACHE[password] = await get_password_hash(password)
    return _PASSWORDS_CACHE[password]


@pytest.fixture(scope="session", autouse=True)
async def prepare_db_and_data():
    """Создает таблицы и заливает статические данные 1 раз для всех тестов"""

    # 1. Пересоздаем структуру
    async with fixture_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # 2. Заливаем "чистые" дефолтные данные один раз!
    # Используем временный sessionmaker только для инициализации
    InitSessionMaker = async_sessionmaker(fixture_engine, expire_on_commit=False)

    async with InitSessionMaker() as session:
        await init_basic_data(session=session, password_hasher=_get_cached_password_hash)
        team = Team(name=TEAM_NAME, invite_code=TEAM_CODE)
        task = Task(
            title="Дефолтная тестовая задача",
            description="Создана автоматически при подготовке БД",
            status=TaskStatus.OPEN,
            author_id=1,
        )
        session.add_all([team, task])
        await session.commit()

    yield  # Здесь побегут все тесты

    # 3. Удаляем структуру в самом конце прогона
    async with fixture_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
