import asyncio
from typing import Callable

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.engine import async_session_maker
from backend.core.security import get_password_hash
from backend.core.constants import RoleName, BusinessElementName
from backend.rbac.schemas import RBACPermissions
from backend.user.models import User, Role
from backend.rbac.models import BusinessElement, AccessRule


async def get_or_create(session, model, **kwargs):
    """Удобный хелпер: ищет запись, если нет - создает"""
    stmt = select(model).filter_by(**kwargs)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()

    if not instance:
        instance = model(**kwargs)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
    return instance


async def _create_access_rule_if_not_exists(
    session: AsyncSession, role_id: int, element_id: int, permissions: RBACPermissions
):
    query = select(AccessRule).where(
        AccessRule.role_id == role_id,
        AccessRule.business_element_id == element_id,
    )
    result = await session.execute(query)
    rule = result.scalar_one_or_none()

    if rule is None:
        rule = AccessRule(
            role_id=role_id,
            business_element_id=element_id,
            **permissions.model_dump(exclude_none=True),
        )
        session.add(rule)


async def init_basic_data(
    session: AsyncSession, password_hasher: Callable = get_password_hash
):
    logger.info("Начинаем инициализацию базовых данных...")
    admin_role = await get_or_create(session, Role, name=RoleName.ADMIN)
    manager_role = await get_or_create(session, Role, name=RoleName.MANAGER)
    user_role = await get_or_create(session, Role, name=RoleName.USER)

    roles_map = {"admin": admin_role, "manager": manager_role, "user": user_role}

    for role in roles_map:
        email = f"{role}@{role}.com"
        query = select(User).filter_by(email=email)
        result = await session.execute(query)
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            new_user = User(
                email=email,
                hashed_password=await password_hasher(role),
                role_id=roles_map[role].id,
                name=role.title(),
            )
            session.add(new_user)
            await session.flush()
            await session.refresh(new_user)

    inactive_user = User(
        email="inactive_user@user.com",
        hashed_password=await password_hasher("user"),
        role_id=roles_map["user"].id,
        name="Inactive user",
        is_active=False,
    )
    session.add(inactive_user)
    await session.flush()
    await session.refresh(inactive_user)

    permissions_map = {
        "admin": RBACPermissions(
            read_all_permission=True,
            update_all_permission=True,
            delete_all_permission=True,
            create_permission=True,
            read_permission=True,
            update_permission=True,
            delete_permission=True,
        ),
        "manager": RBACPermissions(
            read_all_permission=True,
            create_permission=True,
            read_permission=True,
            update_permission=True,
        ),
        "user": RBACPermissions(read_permission=True),
    }

    # Создаем бизнес-элементы для проверки RBAC
    teams_element = await get_or_create(
        session, BusinessElement, name=BusinessElementName.TEAMS
    )

    for key, value in roles_map.items():
        await _create_access_rule_if_not_exists(
            session=session,
            role_id=value.id,
            element_id=teams_element.id,
            permissions=permissions_map[key],
        )
        logger.success(f"Права для {key} на команды успешно выданы.")

    await session.commit()
    logger.info("Инициализация данных успешно завершена!")


async def run_init():
    async with async_session_maker() as session:
        await init_basic_data(session)


if __name__ == "__main__":
    asyncio.run(run_init())
