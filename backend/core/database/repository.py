from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from backend.core.database.models import User, Role
from backend.core.schemas.user import UserRegister
from backend.exceptions import UserExistsError, RoleDoesNotExistsError
from backend.core.security import get_password_hash
from backend.core.config import RoleName


class RegisterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(
        self, user_in: UserRegister, role_name: RoleName = RoleName.USER
    ) -> User:
        await self._check_user_not_exists(user_in=user_in)
        role_id = await self._get_role_id(role_name=role_name)
        new_user = User(
            email=str(user_in.email),
            hashed_password=await get_password_hash(user_in.password),
            name=user_in.name,
            surname=user_in.surname,
            last_name=user_in.last_name,
            role_id=role_id,
            is_active=True,
        )

        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)

        return new_user

    async def _check_user_not_exists(self, user_in: UserRegister) -> bool:
        # Проверка на существование пользователя с таким же email
        query = select(User).where(User.email == user_in.email)
        result = await self.session.execute(query)
        user: User | None = result.scalar_one_or_none()

        if user is not None:
            raise UserExistsError

        return True

    async def _get_role_id(self, role_name: RoleName) -> int:
        stmt = select(Role).where(Role.name == role_name)
        result_role = await self.session.execute(stmt)
        role_obj: Role | None = result_role.scalar_one_or_none()

        if role_obj is None:
            raise RoleDoesNotExistsError

        return role_obj.id
