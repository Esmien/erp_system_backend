from sqlalchemy import select

import pytest

from backend.core.enums import RoleName
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
    "checking_email, is_success_expected",
    [
        ("new_unique_email@test.com", True),
        ("admin@admin.com", False),
    ],
)
async def test_register_user(
    register_repo, user_in, checking_email, is_success_expected
):
    user_in.email = checking_email

    new_user = UserCreateDTO(
        **user_in.model_dump(exclude={"password", "repeat_password"}),
        hashed_password="Fake hash",
        role_id=1,
        is_active=True,
    )

    registered_user = await register_repo.register_user(user_to_register=new_user)

    if is_success_expected:
        assert registered_user is not None
        assert registered_user.id is not None
        assert registered_user.email == checking_email
        assert registered_user.name == user_in.name
        assert registered_user.is_active is True
    else:
        assert registered_user is None
