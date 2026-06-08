import asyncio
from typing import Callable

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.engine import async_session_maker
from backend.core.policies import DEFAULT_POLICIES
from backend.core.security import get_password_hash
from backend.core.constants import RoleName, BusinessElementName
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


async def init_basic_data(
    session: AsyncSession, password_hasher: Callable = get_password_hash
):
    roles_map = {}
    for role_name in RoleName:
        role = await get_or_create(session, Role, name=role_name)
        roles_map[role_name] = role

    elements_map = {}
    for element_name in BusinessElementName:
        element = await get_or_create(session, BusinessElement, name=element_name)
        elements_map[element_name] = element

    for role_name, role_obj in roles_map.items():
        for element_name, element_obj in elements_map.items():
            # Достаем JSON для конкретной роли и сущности (если нет - пустой словарь)
            policies = DEFAULT_POLICIES.get(role_name, {}).get(element_name, {})

            # Проверяем, есть ли уже правило в БД
            stmt = select(AccessRule).where(
                AccessRule.role_id == role_obj.id,
                AccessRule.business_element_id == element_obj.id,
            )
            result = await session.execute(stmt)
            rule = result.scalar_one_or_none()

            if not rule:
                # Создаем новое правило
                rule = AccessRule(
                    role_id=role_obj.id,
                    business_element_id=element_obj.id,
                    policies=policies,
                )
                session.add(rule)
            else:
                # Если правило есть, обновляем JSON (полезно при добавлении новых фич в код)
                rule.policies = policies

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

    stmt = select(User).filter_by(email="inactive_user@user.com")
    result = await session.execute(stmt)
    inactive_user = result.scalar_one_or_none()

    if not inactive_user:
        new_user = User(
            email="inactive_user@user.com",
            hashed_password=await password_hasher("user"),
            role_id=roles_map["user"].id,
            name="Inactive user",
            is_active=False,
        )
        session.add(new_user)
        await session.flush()
        await session.refresh(new_user)

    await session.commit()
    logger.info("Инициализация данных успешно завершена!")


async def run_init():
    async with async_session_maker() as session:
        await init_basic_data(session)


if __name__ == "__main__":
    asyncio.run(run_init())
