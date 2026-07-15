import pytest


@pytest.mark.parametrize(
    "username, password, status",
    [
        ("admin@admin.com", "admin", 200),
        ("admin@admin.com", "1324", 401),
        ("user@user.com", "admin", 401),
        ("inactive_user@user.com", "user", 403),
    ],
)
async def test_get_token_success(client, username, password, status):
    creds = {"username": username, "password": password}

    response = await client.post(url="/api/v1/auth/login/", json=creds)

    assert response.status_code == status

    if response.status_code == 200:
        token = response.json().get("access_token", None)

        parts = token.split(".")
        assert isinstance(token, str)
        assert len(parts) == 3


async def test_restore_user_success(client):
    """Тест успешного восстановления (активации) пользователя"""
    # В наших фикстурах (init_db_fixtures.py) специально создается неактивный юзер
    creds = {"username": "inactive_user@user.com", "password": "user"}

    response = await client.patch("/api/v1/auth/restore/", json=creds)

    assert response.status_code == 200
    assert "успешно восстановлен" in response.json()["message"]


async def test_restore_user_already_active(client):
    """Тест попытки восстановить уже активного пользователя"""
    # Админ изначально активен
    creds = {"username": "admin@admin.com", "password": "admin"}

    response = await client.patch("/api/v1/auth/restore/", json=creds)

    assert response.status_code == 409
    assert response.json()["detail"] == "Пользователь уже активен"


async def test_restore_user_invalid_creds(client):
    """Тест попытки восстановления с неверными данными"""
    creds = {"username": "inactive_user@user.com", "password": "wrong_password"}

    response = await client.patch("/api/v1/auth/restore/", json=creds)

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный логин или пароль"


async def test_logout_success(client):
    """Тест выхода из системы"""
    # Так как у нас висит глобальный оверрайд get_current_user,
    # запрос автоматически считается авторизованным
    headers = {"Authorization": "Bearer test_token_123"}
    response = await client.post("/api/v1/auth/logout/", headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Вы успешно вышли из системы"
