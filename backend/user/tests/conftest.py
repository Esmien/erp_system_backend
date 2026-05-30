import asyncio

import pytest

from backend.core.security import get_password_hash
from backend.user.repository import RegisterRepository, AuthRepository, UserRepository
from backend.user.schemas import UserRegister, UserDTO
from backend.user.service import RegisterService, AuthService, UserService

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
def register_service(mock_uow):
    return RegisterService(uow=mock_uow)


@pytest.fixture
def auth_service(mock_uow):
    return AuthService(uow=mock_uow)


@pytest.fixture
def user_service(mock_uow):
    return UserService(uow=mock_uow)


@pytest.fixture
def user_in():
    return UserRegister(
        email="test@test.com",
        password="test",
        repeat_password="test",
        name="Test",
        surname="Test_1",
        last_name="Test_2",
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
