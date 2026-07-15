import asyncio

import pytest
from sqlalchemy import select

from backend.core.security import get_password_hash
from backend.user.models import User
from backend.user.repository import UserRepository
from backend.user.schemas import UserDTO
from backend.user.service import UserService

HASHED_PASSWORD = asyncio.run(get_password_hash("test"))


@pytest.fixture
def user_repo(db_session):
    return UserRepository(session=db_session)


@pytest.fixture
def user_service(mock_uow, mock_rbac_service):
    return UserService(uow=mock_uow, rbac_service=mock_rbac_service)


@pytest.fixture
def user_to_update():
    return UserDTO(
        id=1,
        email="test@test.com",
        hashed_password=HASHED_PASSWORD,
        name="Test",
        surname="Test_1",
        last_name="Test_2",
        role_id=1,
        is_active=True,
    )


@pytest.fixture
async def test_users(db_session):
    """
    Достает дефолтных пользователей, которые уже были созданы
    при подготовке БД через init_basic_data.
    """
    stmt = select(User).order_by(User.id)
    result = await db_session.execute(stmt)
    return list(result.scalars().all())
