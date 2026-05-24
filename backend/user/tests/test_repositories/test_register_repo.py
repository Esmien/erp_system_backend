from sqlalchemy import select

import pytest

from backend.core.constants import RoleName
from backend.user.models import Role
from backend.user.schemas import UserCreateDTO


@pytest.mark.parametrize(
    "role_name, is_valid",
    [
        (RoleName.ADMIN, True),
        (RoleName.USER, True),
        (RoleName.MANAGER, True),
        ("invalid_role_name", False),
    ],
)
async def test_get_role_id(register_repo, db_session, role_name, is_valid):
    search_value = role_name.value if isinstance(role_name, RoleName) else role_name
    result = await register_repo.get_role_id(role_name=role_name)

    if is_valid:
        stmt = select(Role.id).where(Role.name == search_value)
        real_id = (await db_session.execute(stmt)).scalar_one_or_none()
        assert result is not None
        assert result == real_id
    else:
        assert result is None


@pytest.mark.parametrize(
    "checking_email, expected_result",
    [("admin@admin.com", True), ("test@test.com", False)],
)
async def test_user_exists(register_repo, user_in, checking_email, expected_result):
    user_in.email = checking_email

    result = await register_repo.check_user_exists(user_in=user_in)

    assert result == expected_result


async def test_register_user(register_repo, user_in, user_out):
    new_user = UserCreateDTO(
        **user_in.model_dump(exclude={"password", "repeat_password"}),
        hashed_password="Fake hash",
        role_id=1,
        is_active=True,
    )
    registered_user = await register_repo.register_user(user_to_register=new_user)

    assert registered_user.id is not None
    assert registered_user.email == user_out.email
    assert registered_user.name == user_out.name
    assert registered_user.is_active == user_out.is_active
