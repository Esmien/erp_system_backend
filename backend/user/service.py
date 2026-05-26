from loguru import logger

from backend.core.constants import RoleName
from backend.core.uow import IUnitOfWork
from backend.user.schemas import Token, UserRegister, UserUpdate, UserCreateDTO, UserDTO
from backend.exceptions import (
    UserExistsError,
    UserNotActiveError,
    UserDoesNotExistsError,
    RoleDoesNotExistsError,
    UserAlreadyActiveError,
    InvalidPasswordError,
)
from backend.core.security import (
    verify_password,
    create_access_token,
    get_password_hash,
)


class RegisterService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

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
        async with self.uow:
            # Проверка на существование пользователя с переданным email
            is_user_exists = await self.uow.register.check_user_exists(user_in=user_in)
            if is_user_exists:
                logger.info(f"Пользователь {user_in.email} уже зарегистрирован.")
                raise UserExistsError

            # Защита от присвоения несуществующей роли
            role_id = await self.uow.register.get_role_id(role_name=role_name)
            # Проблема на стороне сервера, роль не найдена
            if not role_id:
                logger.error(f"Ошибка! Роль {role_name} не найдена.")
                raise RoleDoesNotExistsError

            # Собираем модель пользователя со всеми полями
            new_user_dto = UserCreateDTO(
                **user_in.model_dump(exclude={"password", "repeat_password"}),
                hashed_password=await get_password_hash(user_in.password),
                role_id=role_id,
                is_active=True,
            )

            registered_user: UserDTO = await self.uow.register.register_user(
                new_user_dto
            )

            # Регистрируем
            await self.uow.commit()
            logger.success(
                f"Пользователь ID: {registered_user.id}, Email: {registered_user.email} зарегистрирован"
            )
            return registered_user


class AuthService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

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
            InvalidPasswordError - если пароль неверный
        """
        async with self.uow:
            user = await self.uow.auth.get_user(email=email)

        if not user:
            logger.info(f"Пользователь с Email {email} не найден.")
            raise UserDoesNotExistsError

        try:
            await verify_password(
                plain_password=password, hashed_password=user.hashed_password
            )
        except InvalidPasswordError:
            logger.info(f"Введен неверный пароль для пользователя {email}.")
            raise

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
            UserDoesNotExistsError - если пользователь не найден
        """
        # Проверяем флаг активности пользователя
        if self._check_user_active(user=user):
            logger.info(f"Пользователь {user.name} уже активен.")
            raise UserAlreadyActiveError

        async with self.uow:
            activated_user = await self.uow.auth.activate_user(user_email=user.email)

            if not activated_user:
                logger.info(f"Пользователь с {user.email} не существует.")
                raise UserDoesNotExistsError

            await self.uow.commit()
            logger.success(f"Пользователь {user.name} успешно активирован.")

        return activated_user

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
            logger.info(f"Пользователь {user.name} не активен")
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
        async with self.uow:
            user = await self.uow.auth.get_user_and_role_by_user_id(user_id)

        if not user:
            logger.info(f"Пользователь с ID {user_id} не найден.")
            raise UserDoesNotExistsError
        if not self._check_user_active(user):
            logger.info(f"Пользователь с ID {user_id} не активен.")
            raise UserNotActiveError

        logger.success(f"Пользователь с ID {user_id} успешно получен. ({user.email})")
        return user


class UserService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

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
            logger.info(
                f"Нет данных для обновления пользователя ID: {user.id}, Email: {user.email}."
            )
            return user

        async with self.uow:
            updated_user = await self.uow.users.update_user(
                user_id=user.id, update_dict=update_dict
            )

            if not updated_user:
                logger.info(
                    f"Не найден пользователь для обновления, ID: {user.id}, Email: {user.email}."
                )
                raise UserDoesNotExistsError

            await self.uow.commit()

        logger.success(
            f"Пользователь ID: {user.id}, Email: {user.email} успешно обновлен."
        )
        return updated_user

    async def soft_delete_profile(self, user: UserDTO) -> None:
        """
        Мягко удаляет пользователя (деактивирует)

        Args:
            user - модель пользователя для удаления

        Raises:
            UserDoesNotExists - если пользователь не найден
        """
        async with self.uow:
            deactivated_user = await self.uow.users.soft_delete_user(user_id=user.id)

            if not deactivated_user:
                logger.info(
                    f"Не найден пользователь для удаления, ID: {user.id}, Email: {user.email}."
                )
                raise UserDoesNotExistsError

            await self.uow.commit()
            logger.success(
                f"Пользователь ID: {deactivated_user.id}, Email: {deactivated_user.email} успешно удален (деактивирован)."
            )
