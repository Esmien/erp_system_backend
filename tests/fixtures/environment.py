from sqlalchemy import NullPool, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload

from backend.api.dependencies.permissions import get_current_user
from backend.api.dependencies.uow import get_uow
from backend.api.main import app
from backend.core.uow import UnitOfWork
from backend.user.models import User
from backend.user.schemas import UserDTO

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_business_db"

fixture_engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)

fixture_async_session_maker = async_sessionmaker(
    bind=fixture_engine, expire_on_commit=False, autoflush=False
)


async def override_get_session():
    async with fixture_async_session_maker() as session:
        yield session


async def override_get_current_user():
    async with fixture_async_session_maker() as session:
        stmt = (
            select(User)
            .where(User.email == "admin@admin.com")
            .options(selectinload(User.role))
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return UserDTO.model_validate(user) if user else None


class TestUnitOfWork(UnitOfWork):
    def __init__(self):
        super().__init__()
        self.session_factory = fixture_async_session_maker


def override_get_uow():
    return TestUnitOfWork()


app.dependency_overrides[get_uow] = override_get_uow
app.dependency_overrides[get_current_user] = override_get_current_user
