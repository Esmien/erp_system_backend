from backend.api.dependencies.reg_and_auth import (
    get_register_service,
)
from backend.api.main import app
from backend.exceptions import RoleDoesNotExistsError


async def test_register_success(client, data_for_register, success_register_response):
    response = await client.post("/v1/auth/register", json=data_for_register)

    assert response.status_code == 201
    assert response.json() == success_register_response


async def test_register_already_exists(
    client, data_for_register, reg_user_already_exists_response
):
    await client.post("/v1/auth/register", json=data_for_register)
    response = await client.post("/v1/auth/register", json=data_for_register)

    assert response.status_code == 400
    assert response.json() == reg_user_already_exists_response


class FakeRegisterService:
    async def register_user(self, user_in):
        raise RoleDoesNotExistsError


async def override_register_service():
    return FakeRegisterService()  # noqa: F821


async def test_register_role_not_exists(
    client, data_for_register, reg_role_not_exists_response
):
    old_dep = app.dependency_overrides.get(get_register_service)
    app.dependency_overrides[get_register_service] = override_register_service

    response = await client.post("/v1/auth/register", json=data_for_register)

    if old_dep is not None:
        app.dependency_overrides[get_register_service] = old_dep
    else:
        del app.dependency_overrides[get_register_service]

    assert response.status_code == 503
    assert response.json() == reg_role_not_exists_response
