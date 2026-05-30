import pytest
from sqlalchemy import select

from backend.user.models import User


@pytest.mark.parametrize(
    "email, exists",
    [
        ("admin@admin.com", True),
        ("manager@manager.com", True),
        ("user@user.com", True),
        ("invalid_email@user.com", False),
    ],
)
async def test_get_user_and_role_by_user_id(auth_repo, db_session, email, exists):
    stmt = select(User.id).where(User.email == email)
    real_id = (await db_session.execute(stmt)).scalar_one_or_none()

    testing_id = real_id if real_id is not None else 99999

    user = await auth_repo.get_user_and_role_by_user_id(user_id=testing_id)

    if exists:
        assert user is not None
        assert user.id == testing_id
        assert user.role is not None
    else:
        assert user is None


@pytest.mark.parametrize(
    "email, exists",
    [
        ("admin@admin.com", True),
        ("manager@manager.com", True),
        ("user@user.com", True),
        ("invalid_email@user.com", False),
    ],
)
async def test_get_user(auth_repo, email, exists):
    user = await auth_repo.get_user(email)

    if exists:
        assert user is not None
        assert user.email == email
    else:
        assert user is None


@pytest.mark.parametrize("initial_active_status", [True, False])
async def test_activate_user(auth_repo, db_session, initial_active_status):
    testing_email = "admin@admin.com"
    stmt = select(User).where(User.email == testing_email)
    user = (await db_session.execute(stmt)).scalar_one()
    user.is_active = initial_active_status

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    activated_user = await auth_repo.activate_user(user_email=testing_email)

    assert activated_user.is_active is True
    assert user.is_active is True


async def test_goy_none_user(auth_repo):
    user = await auth_repo.activate_user(user_email="fake_user@fake.com")

    assert user is None