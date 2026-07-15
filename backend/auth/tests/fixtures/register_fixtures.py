import asyncio

import pytest

from backend.auth.repository import RegisterRepository
from backend.auth.schemas import UserRegister
from backend.auth.service import RegisterService
from backend.core.security import get_password_hash
from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.user.schemas import UserDTO

HASHED_PASSWORD = asyncio.run(get_password_hash("test"))


@pytest.fixture
def register_repo(db_session):
    return RegisterRepository(session=db_session)


@pytest.fixture
def register_service(mock_uow, mock_rbac_service, mock_redis):
    return RegisterService(uow=mock_uow, rbac_service=mock_rbac_service, redis=mock_redis)


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
def base_user_data():
    return {
        "email": "user1@example.com",
        "name": "Иван",
        "surname": "Иванович",
        "last_name": "Иванов",
    }


@pytest.fixture
def valid_data_for_register(base_user_data):
    user_data = base_user_data.copy()
    additional_fields = {
        "password": "secret_password",
        "repeat_password": "secret_password",
        "register_code": "000000",
    }
    user_data.update(**additional_fields)

    return user_data


@pytest.fixture
def data_for_register_with_mismatch_passwords(valid_data_for_register):
    invalid_data_for_register = valid_data_for_register.copy()
    invalid_data_for_register["repeat_password"] = "another_password"

    return invalid_data_for_register


@pytest.fixture
def success_register_response(base_user_data):
    user_data = base_user_data.copy()
    additional_fields = {
        "team_id": None,
        "id": 5,
        "is_active": True,
        "role": {"name": "user", "id": 3},
    }
    user_data.update(**additional_fields)

    return user_data


@pytest.fixture
def reg_user_already_exists_response():
    content = ErrorResponseSchema(detail="Пользователь с таким email уже зарегистрирован!", status_code=400)
    return content.model_dump()


@pytest.fixture
def reg_role_not_exists_response():
    content = ErrorResponseSchema(detail="Запрашиваемая роль не найдена, обратитесь в поддержку", status_code=500)
    return content.model_dump()


@pytest.fixture
def mismatch_passwords_response():
    content = ErrorResponseSchema(detail="Пароли не совпадают!", status_code=400)
    return content.model_dump()
