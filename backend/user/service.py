from datetime import UTC, datetime

import jwt
from loguru import logger
from redis.asyncio import Redis

from backend.core.config import settings
from backend.core.enums import Action, BusinessElementName, RoleName
from backend.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from backend.core.uow import IUnitOfWork
from backend.exceptions import (
    BadCredentialsError,
    InvalidPasswordError,
    RoleDoesNotExistError,
    UnexpectedError,
    UserAlreadyActiveError,
    UserDoesNotExistError,
    UserExistsError,
    UserNotActiveError,
)
from backend.rbac.schemas import AccessContextDTO
from backend.rbac.service import RbacService
from backend.user.schemas import Token, UserCreateDTO, UserDTO, UserRegister, UserUpdate


class RegisterService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def register_user(self, user_in: UserRegister, role_name: RoleName = RoleName.USER) -> UserDTO:
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
        # Защита от присвоения несуществующей роли
        role_id = await self.uow.register.get_role_id(role_name=role_name)
        # Проблема на стороне сервера, роль не найдена
        if not role_id:
            logger.error(f"Ошибка! Роль {role_name} не найдена.")
            raise RoleDoesNotExistError("Запрашиваемая роль не найдена, обратитесь в поддержку")

        # Собираем модель пользователя со всеми полями
        new_user_dto = UserCreateDTO(
            **user_in.model_dump(exclude={"password", "repeat_password"}),
            hashed_password=await get_password_hash(user_in.password),
            role_id=role_id,
            is_active=True,
        )

        registered_user = await self.uow.register.register_user(new_user_dto)

        if not registered_user:
            logger.info(f"Пользователь {user_in.email} уже зарегистрирован.")
            raise UserExistsError("Пользователь с таким email уже зарегистрирован!")

        # Регистрируем
        await self.uow.commit()
        logger.info(f"Пользователь ID: {registered_user.id}, Email: {registered_user.email} зарегистрирован")
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
            BadCredentialsError - если почта или пароль неверные
        """
        user = await self.uow.auth.get_user(email=email)

        if not user:
            logger.info(f"Пользователь с Email {email} не найден.")
            raise BadCredentialsError("Неверный логин или пароль")

        try:
            await verify_password(plain_password=password, hashed_password=user.hashed_password)
        except InvalidPasswordError:
            logger.info(f"Введен неверный пароль для пользователя {email}.")
            raise BadCredentialsError("Неверный логин или пароль") from None

        return user

    async def authenticate_by_telegram(self, tg_id: int) -> UserDTO:
        """
        Тихая авторизация по Telegram ID

        Args:
            tg_id - Telegram ID аользователя

        Returns:
            Модель зарегистрированного и активного пользователя
        """
        user = await self.uow.auth.get_user(tg_id=tg_id)

        if not user:
            logger.info(f"Пользователь с Telegram ID {tg_id} не найден.")
            raise BadCredentialsError("Telegram аккаунт не привязан")

        if not self._check_user_active(user):
            logger.info(f"Пользователь {user.email} деактивирован, но пытался войти через ТГ.")
            raise UserNotActiveError("Аккаунт удален или деактивирован")

        return user

    async def link_telegram_account(self, email: str, password: str, tg_id: int) -> UserDTO:
        """
        Единоразовая привязка Telegram ID к аккаунту

        Args:
            email - почта пользователя
            password - пароль пользователя
            tg_id - TelegramID пользователя для привязки

        Returns:
            Модель пользователя с привязанным TelegramID
        """
        user = await self.check_users_creds(email=email, password=password)

        if getattr(user, "tg_id", None):
            logger.warning(f"У пользователя {email} уже привязан Telegram. TgID перезаписан на {tg_id}.")

        updated_user = await self.uow.users.update_user(user_id=user.id, update_dict={"tg_id": tg_id})

        if not updated_user:
            raise UnexpectedError("Неожиданная ошибка при привязке TelegramID к пользователю")

        await self.uow.commit()
        logger.info(f"Пользователь {user.email} успешно привязал Telegram ID: {tg_id}")

        return updated_user

    async def unlink_telegram_account(self, user: UserDTO) -> None:
        await self.uow.users.update_user(user_id=user.id, update_dict={"tg_id": None})
        await self.uow.commit()
        logger.info(f"Пользователь {user.email} успешно отвязал ТГ-аккаунт {user.tg_id}")

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
            raise UserAlreadyActiveError("Пользователь уже активен")

        activated_user = await self.uow.auth.activate_user(
            user_email=str(user.email)
        )  # обернут в str чтобы IDE не ругалась

        if not activated_user:
            logger.info(f"Пользователь с {user.email} не существует.")
            raise UserDoesNotExistError

        await self.uow.commit()
        logger.info(f"Пользователь {user.name} успешно активирован.")

        return activated_user

    def get_auth_token(self, user: UserDTO) -> Token:
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
            raise UserNotActiveError("Аккаунт удален или деактивирован")

        # Генерируем токен
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    async def refresh_tokens(self, refresh_token: str, redis: Redis) -> Token:
        """
        Метод для обработки refresh токена

        Args:
            refresh_token - refresh токен для обработки
            redis - инстанс запущенного Redis

        Returns:
            Новая пара access и refresh токенов

        Raises:
            BadCredentialsError - если исходный токен не refresh, он в блэклисте или невалиден
        """
        try:
            payload = jwt.decode(
                jwt=refresh_token,
                key=settings.security.SECRET_KEY,
                algorithms=[settings.security.ALGORITHM],
            )
            # Проверяем тип токена
            if payload.get("type") != "refresh":
                raise BadCredentialsError("Неверный тип токена")

            user_id = payload.get("sub")
            jti = payload.get("jti")

            # Проверка на блэклист
            if await redis.get(f"jwt:blacklist:{jti}"):
                raise BadCredentialsError("Токен отозван")

            user = await self.get_active_user_by_id(int(user_id))

            # Добавляем текущий refresh токен в блэклист
            await self.logout(token=refresh_token, redis=redis)

            return self.get_auth_token(user=user)

        except jwt.PyJWTError:
            raise BadCredentialsError("Недействительный токен") from None

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
        user = await self.uow.auth.get_user_and_role_by_user_id(user_id)

        if not user:
            logger.info(f"Пользователь с ID {user_id} не найден.")
            raise UserDoesNotExistError
        if not self._check_user_active(user):
            logger.info(f"Пользователь с ID {user_id} не активен.")
            raise UserNotActiveError

        logger.info(f"Пользователь с ID {user_id} успешно получен. ({user.email})")
        return user

    @staticmethod
    async def logout(token: str | None, redis: Redis) -> None:
        """
        Разлогинивает пользователя с добавлением JWT в блэклист

        Args:
            token - JWT-токен из заголовка
            redis - инстанс Redis для записи токена в него
        """
        try:
            # Декодируем токен
            payload = jwt.decode(
                jwt=token,
                key=settings.security.SECRET_KEY,
                algorithms=[settings.security.ALGORITHM],
            )
            jti = payload.get("jti")
            exp = payload.get("exp")

            # Вычисляем остаток времени жизни JWT для TTL в блэклисте
            now = int(datetime.now(tz=UTC).timestamp())
            ttl = exp - now

            if ttl > 0:
                # Отправляем в Redis
                await redis.setex(f"jwt:blacklist:{jti}", ttl, "revoked")
                logger.debug(f"Токен {jti} успешно добавлен в блэклист на {ttl} сек.")

        except jwt.DecodeError:
            # Если условие не выполнилось и токен оказался абсолютно "левым"
            logger.error("Ошибка декодирования токена при попытке логаута")

            return


class UserService:
    def __init__(self, uow: IUnitOfWork, rbac_service: RbacService):
        self.uow = uow
        self.rbac = rbac_service

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
            logger.info(f"Нет данных для обновления пользователя ID: {user.id}, Email: {user.email}.")
            return user

        # Проверка прав - обновлять профили могут либо владельцы, либо руководители
        await self.rbac.enforce_permission(
            user=user,
            business_element_name=BusinessElementName.USERS,
            action=Action.UPDATE,
            context=AccessContextDTO(is_author=True),
            error_msg="Недостаточно прав для обновления профиля",
        )

        updated_user = await self.uow.users.update_user(user_id=user.id, update_dict=update_dict)

        if not updated_user:
            logger.info(f"Не найден пользователь для обновления, ID: {user.id}, Email: {user.email}.")
            raise UserDoesNotExistError

        await self.uow.commit()

        logger.info(f"Пользователь ID: {user.id}, Email: {user.email} успешно обновлен.")
        return updated_user

    async def soft_delete_profile(self, user: UserDTO) -> None:
        """
        Мягко удаляет пользователя (деактивирует)

        Args:
            user - модель пользователя для удаления

        Raises:
            UserDoesNotExists - если пользователь не найден
        """
        # Проверка прав - удалить можно только свой профиль. Если руководитель, то любой
        await self.rbac.enforce_permission(
            user=user,
            business_element_name=BusinessElementName.USERS,
            action=Action.DELETE,
            context=AccessContextDTO(is_author=True),
            error_msg="Недостаточно прав для удаления профиля",
        )

        deactivated_user = await self.uow.users.soft_delete_user(user_id=user.id)

        if not deactivated_user:
            logger.info(f"Не найден пользователь для удаления, ID: {user.id}, Email: {user.email}.")
            raise UserDoesNotExistError

        await self.uow.commit()
        logger.info(f"Пользователь ID: {deactivated_user.id}, Email: {deactivated_user.email} успешно деактивирован.")
