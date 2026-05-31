import pytest


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
    return {"detail": "Пользователь с таким email уже зарегистрирован!"}


@pytest.fixture
def reg_role_not_exists_response():
    return {"detail": "Запрашиваемая роль не найдена, обратитесь в поддержку"}


@pytest.fixture
def mismatch_passwords_response():
    return {"detail": "Пароли не совпадают!"}
