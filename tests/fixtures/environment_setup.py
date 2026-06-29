from sqlalchemy import NullPool, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from backend.core.config import settings
from backend.core.uow import UnitOfWork
from backend.user.models import User
from backend.user.schemas import UserDTO

TEST_DB_URL = settings.db.test_database_url

fixture_engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)

fixture_async_session_maker = async_sessionmaker(bind=fixture_engine, expire_on_commit=False, autoflush=False)


async def override_get_admin_user():
    async with fixture_async_session_maker() as session:
        stmt = select(User).where(User.email == "admin@admin.com").options(selectinload(User.role))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return UserDTO.model_validate(user) if user else None


async def override_get_regular_user():
    """Вспомогательная функция для переключения на обычного пользователя без прав"""
    async with fixture_async_session_maker() as session:
        stmt = select(User).where(User.email == "user@user.com").options(selectinload(User.role))
        result = await session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return UserDTO.model_validate(user_model) if user_model else None


class TestUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def override_get_uow(db_session):
    return TestUnitOfWork(session=db_session)
