import pytest


@pytest.fixture
def valid_data_for_register():
    return {
        "email": "user1@example.com",
        "name": "Иван",
        "surname": "Иванович",
        "last_name": "Иванов",
        "password": "secret_password",
        "repeat_password": "secret_password",
    }


@pytest.fixture
def data_for_register_with_mismatch_passwords():
    return {
        "email": "user1@example.com",
        "name": "Иван",
        "surname": "Иванович",
        "last_name": "Иванов",
        "password": "secret_password",
        "repeat_password": "secret_password1",
    }


@pytest.fixture
def success_register_response():
    return {
        "email": "user1@example.com",
        "name": "Иван",
        "surname": "Иванович",
        "last_name": "Иванов",
        "team_id": None,
        "id": 5,
        "is_active": True,
        "role": {"name": "user", "id": 3},
    }


@pytest.fixture
def reg_user_already_exists_response():
    return {"detail": "Пользователь с таким email уже зарегистрирован!"}


@pytest.fixture
def reg_role_not_exists_response():
    return {"detail": "Запрашиваемая роль не найдена, обратитесь в поддержку"}


@pytest.fixture
def mismatch_passwords_response():
    return {"detail": "Пароли не совпадают!"}