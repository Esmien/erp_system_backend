import asyncio

import pytest
from sqlalchemy import select

from backend.core.security import get_password_hash
from backend.user.models import User
from backend.user.repository import AuthRepository, RegisterRepository, UserRepository
from backend.user.schemas import UserDTO, UserRegister
from backend.user.service import AuthService, RegisterService, UserService

HASHED_PASSWORD = asyncio.run(get_password_hash("test"))


@pytest.fixture
def register_repo(db_session):
    return RegisterRepository(session=db_session)


@pytest.fixture
def auth_repo(db_session):
    return AuthRepository(session=db_session)


@pytest.fixture
def user_repo(db_session):
    return UserRepository(session=db_session)


@pytest.fixture
def register_service(mock_uow, mock_rbac_service, mock_redis):
    return RegisterService(uow=mock_uow, rbac_service=mock_rbac_service, redis=mock_redis)


@pytest.fixture
def auth_service(mock_uow, mock_redis):
    return AuthService(uow=mock_uow, redis=mock_redis)


@pytest.fixture
def user_service(mock_uow, mock_rbac_service):
    return UserService(uow=mock_uow, rbac_service=mock_rbac_service)


@pytest.fixture
def user_in():
    return UserRegister(
        email="test@test.com",
        password="test",
        repeat_password="test",
        name="Test",
        surname="Test_1",
        last_name="Test_2",
        register_code="000000",
    )


@pytest.fixture
def user_out():
    return UserDTO(
        id=5,
        email="test@test.com",
        hashed_password=HASHED_PASSWORD,
        name="Test",
        surname="Test_1",
        last_name="Test_2",
        role_id=1,
        is_active=True,
    )


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
