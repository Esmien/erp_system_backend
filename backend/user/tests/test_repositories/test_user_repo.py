import pytest
from sqlalchemy import select

from backend.user.models import User


@pytest.mark.parametrize(
    "update_dict",
    [
        {
            "name": "Updated Name",
            "surname": "Updated Surname",
            "last_name": "Updated Last Name",
        },
        {"name": "Updated Name", "surname": "Updated Surname"},
        {"last_name": "Updated Last Name"},
        {},
    ],
)
async def test_update_user(user_repo, db_session, update_dict):

    stmt = select(User).where(User.email == "user@user.com")
    user = (await db_session.execute(stmt)).scalar_one()

    original_name = user.name
    original_surname = user.surname
    original_last_name = user.last_name

    await user_repo.update_user(user_id=user.id, update_dict=update_dict)
    await db_session.refresh(user)

    assert user.name == update_dict.get("name", original_name)
    assert user.surname == update_dict.get("surname", original_surname)
    assert user.last_name == update_dict.get("last_name", original_last_name)


async def test_soft_delete_user(user_repo, db_session):
    stmt = select(User).where(User.email == "user@user.com")
    user = (await db_session.execute(stmt)).scalar_one()

    assert user.is_active is True

    await user_repo.soft_delete_user(user_id=user.id)
    await db_session.refresh(user)

    assert user.is_active is False


async def test_got_none_user(user_repo):
    none_user_from_update = await user_repo.update_user(user_id=9999, update_dict={})
    none_user_from_soft_delete = await user_repo.soft_delete_user(user_id=9999)

    assert none_user_from_update is None
    assert none_user_from_soft_delete is None