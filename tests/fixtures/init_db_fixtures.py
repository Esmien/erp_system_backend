import pytest
from sqlalchemy import text


from backend.core.database.engine import Base
from backend.core.database.init_db import init_basic_data
from backend.core.security import get_password_hash
from backend.team.models import Team
from tests.fixtures.environment import (
    fixture_engine,
    fixture_async_session_maker,
)

TEAM_NAME = "Dummy name"
TEAM_CODE = "111111"

_PASSWORDS_CACHE: dict[str, str] = {}


async def _get_cached_password_hash(password: str) -> str:
    """Возвращает закешированный хеш или генерирует новый, если его еще нет"""
    if password not in _PASSWORDS_CACHE:
        _PASSWORDS_CACHE[password] = await get_password_hash(password)
    return _PASSWORDS_CACHE[password]


# Фикстура для структуры БД (выполняется 1 раз за сессию)
@pytest.fixture(scope="session", autouse=True)
async def prepare_schema():
    """Создает таблицы перед началом тестов и удаляет в конце"""
    async with fixture_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with fixture_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function", autouse=True)
async def prepare_data():
    """Очищает таблицы и заливает базовые данные для каждого теста"""

    # 2.1 Жестко очищаем все таблицы
    async with fixture_engine.begin() as conn:
        # Собираем имена всех таблиц из метадаты
        table_names = ", ".join(Base.metadata.tables.keys())

        if table_names:
            # RESTART IDENTITY - сбрасывает счетчики (id=1)
            # CASCADE - игнорирует foreign keys и сносит связанные данные
            await conn.execute(
                text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;")
            )

    # 2.2 Заливаем "чистые" дефолтные данные
    async with fixture_async_session_maker() as session:
        await init_basic_data(
            session=session, password_hasher=_get_cached_password_hash
        )
        team = Team(name=TEAM_NAME, invite_code=TEAM_CODE)
        session.add(team)
        await session.commit()
