from loguru import logger

from backend.core.config import RoleName
from backend.core.database.models.users import User
from backend.core.database.repository import AuthRepository, RegisterRepository
from backend.core.schemas.user import Token, UserRegister
from backend.exceptions import (
    UserExistsError,
    UserNotActiveError,
)
from backend.core.security import (
    verify_password,
    create_access_token,
    get_password_hash,
)


class RegisterService:
    def __init__(self, repo: RegisterRepository):
        self.repo = repo

    async def register_user(
        self, user_in: UserRegister, role_name: RoleName = RoleName.USER
    ) -> User:
        await self.repo.check_user_not_exists(user_in=user_in)
        role_id = await self.repo.get_role_id(role_name=role_name)

        new_user = User(
            email=str(user_in.email),
            hashed_password=await get_password_hash(user_in.password),
            name=user_in.name,
            surname=user_in.surname,
            last_name=user_in.last_name,
            role_id=role_id,
            is_active=True,
        )

        return await self.repo.register_user(new_user)


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    @staticmethod
    def _check_user_active(user: User) -> bool:
        return user.is_active

    async def check_users_creds(self, email: str, password: str) -> User:
        """
        Проверка учетных данных пользователя.
        Используется при аутентификации и восстановлении пользователя

        Args:
            email - Электронная почта пользователя
            password - Пароль пользователя

        Raises:
            Исключения приходят снизу.
            UserDoesNotExistsError - если пользователь с этим email не найден
            InvalidPasswordError - если пароль неверный

        Returns:
            Объект пользователя, если учетные данные верны.
        """
        user: User = await self.repo.get_user(email=email)
        await verify_password(password, user.hashed_password)

        return user

    async def activate_user(self, user: User) -> User:
        if self._check_user_active(user=user):
            logger.warning(f"Пользователь {user.name} уже активен")
            raise UserExistsError

        user.is_active = True

        return await self.repo.activate_user(user=user)

    async def get_auth_token(self, user: User) -> Token:
        if not self._check_user_active(user=user):
            logger.warning(f"Пользователь {user.name} не активен")
            raise UserNotActiveError

        access_token = create_access_token(data={"sub": str(user.id)})

        return Token(access_token=access_token, token_type="bearer")
