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

    response = await client.post(url="/api/v1/auth/login", data=creds)

    assert response.status_code == status

    if response.status_code == 200:
        token = response.json().get("access_token", None)

        parts = token.split(".")
        assert isinstance(token, str)
        assert len(parts) == 3
