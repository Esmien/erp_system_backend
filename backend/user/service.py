from loguru import logger

from backend.core.constants import RoleName
from backend.user.repository import RegisterRepository, AuthRepository, UserRepository
from backend.user.schemas import Token, UserRegister, UserUpdate, UserCreateDTO, UserDTO
from backend.exceptions import (
    UserExistsError,
    UserNotActiveError,
    UserDoesNotExistsError,
    RoleDoesNotExistsError,
    UserAlreadyActiveError,
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
    ) -> UserDTO:
        """
        Регистрирует пользователя, присваивая ему роль

        Args:
            user_in - Pydantic-модель пользователя с данными для регистрации
            role_name - присваиваемая роль (по умолчанию User)

        Returns:
            Модель зарегистрированного пользователя

        Raises:
            UserExistsError - если пользователь существует
            RoleDoesNotExistsError - присваиваемая роль не найдена
        """
        # Проверка на существование пользователя с переданным email
        is_user_exists = await self.repo.check_user_exists(user_in=user_in)

        if is_user_exists:
            raise UserExistsError

        # Защита от присвоения несуществующей роли
        role_id = await self.repo.get_role_id(role_name=role_name)

        # Проблема на стороне сервера, роль не найдена
        if not role_id:
            raise RoleDoesNotExistsError

        # Собираем модель пользователя со всеми полями
        new_user = UserCreateDTO(
            **user_in.model_dump(exclude={"password", "repeat_password"}),
            hashed_password=await get_password_hash(user_in.password),
            role_id=role_id,
            is_active=True,
        )

        # Регистрируем
        return await self.repo.register_user(new_user)


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    @staticmethod
    def _check_user_active(user: UserDTO) -> bool:
        """Возвращает True если пользователь активен (is_active=True)"""
        return user.is_active

    async def check_users_creds(self, email: str, password: str) -> UserDTO:
        """
        Проверка учетных данных пользователя.
        Используется при аутентификации и восстановлении пользователя

        Args:
            email - Электронная почта пользователя
            password - Пароль пользователя

        Returns:
            Объект пользователя, если учетные данные верны

        Raises:
            UserDoesNotExistsError - если пользователь с этим email не найден
            InvalidPasswordError - если пароль неверный (приходит от verify_password)
        """
        user = await self.repo.get_user(email=email)

        if not user:
            raise UserDoesNotExistsError

        await verify_password(
            plain_password=password, hashed_password=user.hashed_password
        )

        return user

    async def activate_user(self, user: UserDTO) -> UserDTO:
        """
        Активирует аккаунт пользователя

        Args:
            user - модель пользователя

        Returns:
            Модель пользователя с is_active=True

        Raises:
            UserAlreadyActiveError - если пользователь активен
        """
        if self._check_user_active(user=user):
            logger.warning(f"Пользователь {user.name} уже активен")
            raise UserAlreadyActiveError

        return await self.repo.activate_user(user_email=user.email)

    async def get_auth_token(self, user: UserDTO) -> Token:
        """
        Получает JWT-токен для пользователя

        Args:
            user - запрашивающий токен пользователь

        Returns:
            Token(access_token=JWT-строка, token_type="bearer")

        Raises:
            UserNotActiveError - если запрашивающий юзер неактивен
        """
        # Если пользователь неактивен, токен ему не положен
        if not self._check_user_active(user=user):
            logger.warning(f"Пользователь {user.name} не активен")
            raise UserNotActiveError

        # Генерируем токен
        access_token = create_access_token(data={"sub": str(user.id)})

        return Token(access_token=access_token, token_type="bearer")

    async def get_active_user_by_id(self, user_id: int) -> UserDTO:
        """
        Получает активного пользователя по ID

        Args:
            user_id - искомый ID

        Returns:
            Модель найденного пользователя

        Raises:
            UserDoesNotExistsError - если пользователь не найден
            UserNotActiveError - если найден, но неактивен
        """
        user = await self.repo.get_user_and_role_by_user_id(user_id)

        if not user:
            raise UserDoesNotExistsError
        if not self._check_user_active(user):
            raise UserNotActiveError

        return user


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def update_profile(self, user: UserDTO, update_data: UserUpdate) -> UserDTO:
        """
        Обновляет данные пользователя (ФИО)

        Args:
            user - модель пользователя для обновления
            update_data - данные, которые пользователь хочет обновить

        Returns:
            Обновленная модель пользователя (или исходная, если данных для обновления нет)

        Raises:
            UserDoesNotExistsError - если репозиторий не нашел пользователя
        """
        # Сериализуем данные для дальнейшей обработки в репозитории, исключая не заданные поля
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            return user

        updated_user = await self.repo.update_user(
            user_id=user.id, update_dict=update_dict
        )

        if not updated_user:
            raise UserDoesNotExistsError

        return updated_user

    async def soft_delete_profile(self, user: UserDTO) -> None:
        """Мягко удаляет пользователя (деактивирует)"""
        await self.repo.soft_delete_user(user_id=user.id)
