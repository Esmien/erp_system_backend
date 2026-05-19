from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.database.models import User, Role
from backend.core.schemas.user import UserRegister
from backend.exceptions import (
    UserExistsError,
    RoleDoesNotExistsError,
)
from backend.core.config import RoleName


class RegisterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, new_user) -> User:

        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)

        return new_user

    async def check_user_not_exists(self, user_in: UserRegister) -> bool:
        # Проверка на существование пользователя с таким же email
        query = select(User).where(User.email == user_in.email)
        result = await self.session.execute(query)
        user: User | None = result.scalar_one_or_none()

        if user is not None:
            raise UserExistsError

        return True

    async def get_role_id(self, role_name: RoleName) -> int:
        stmt = select(Role).where(Role.name == role_name)
        result_role = await self.session.execute(stmt)
        role_obj: Role | None = result_role.scalar_one_or_none()

        if role_obj is None:
            raise RoleDoesNotExistsError

        return role_obj.id


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_and_role_by_user_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.role))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user(self, email) -> User | None:
        # Проверяем совпадение пароля и наличие пользователя в БД
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def activate_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user
