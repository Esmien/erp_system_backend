import secrets
import string
from datetime import UTC, datetime

import jwt
from loguru import logger
from redis.asyncio import Redis

from backend.auth.schemas import RegisterCode, Token, UserRegister
from backend.core.config import settings
from backend.core.enums import Action, BusinessElementName, RoleName
from backend.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from backend.core.uow import IUnitOfWork
from backend.exceptions import (
    AccessDeniedError,
    BadCredentialsError,
    InvalidPasswordError,
    RoleDoesNotExistError,
    UnexpectedError,
    UserAlreadyActiveError,
    UserDoesNotExistError,
    UserExistsError,
    UserNotActiveError,
)
from backend.rbac.service import RbacService
from backend.user.schemas import RoleForCodeDTO, UserCreateDTO, UserDTO


class RegisterService:
    def __init__(self, uow: IUnitOfWork, redis: Redis, rbac_service: RbacService):
        self.uow = uow
        self.redis = redis
        self.rbac = rbac_service

    async def get_role_by_register_code(self, code: str) -> RoleName:
        """
        Получает название роли из инвайт-кода

        Args:
            code - код для проверки

        Returns:
            Название роли, вшитое в код регистрации
        """
        redis_reg_code_key = settings.redis_keys.key_reg_code(code=code)
        raw_role = await self.redis.get(name=redis_reg_code_key)

        if not raw_role:
            raise AccessDeniedError("Код недействителен или просрочен")

        # Успокаиваем линтер и страхуемся на случай отсутствия decode_responses
        if isinstance(raw_role, bytes):
            raw_role = raw_role.decode("utf-8")

        if raw_role not in RoleName:
            raise UnexpectedError(f"Роли с названием {raw_role} не существует")

        return RoleName(raw_role)

    async def generate_registration_code(self, user: UserDTO, role: RoleForCodeDTO) -> RegisterCode:
        await self.rbac.enforce_permission(
            user=user,
            business_element_name=BusinessElementName.USERS,
            action=Action.CREATE,
            error_msg="Недостаточно прав для создания кода для регистрации",
        )

        alphabet = string.ascii_uppercase + string.digits
        new_code = "".join(secrets.choice(alphabet) for _ in range(6))

        # Сохраняем в Redis с TTL на 24 часа (86400 секунд)

        redis_reg_code_key = settings.redis_keys.key_reg_code(code=new_code)
        await self.redis.setex(name=redis_reg_code_key, time=86400, value=RoleName(role.name))
        return RegisterCode(register_code=new_code)

    async def register_user(self, user_in: UserRegister) -> UserDTO:
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
        role_name = await self.get_role_by_register_code(code=user_in.register_code)

        # Защита от присвоения несуществующей роли
        role_id = await self.uow.register.get_role_id(role_name=role_name)
        # Проблема на стороне сервера, роль не найдена
        if not role_id:
            logger.error(f"Ошибка! Роль {role_name} не найдена.")
            raise RoleDoesNotExistError("Запрашиваемая роль не найдена, обратитесь в поддержку")

        # Собираем модель пользователя со всеми полями
        new_user_dto = UserCreateDTO(
            **user_in.model_dump(exclude={"password", "repeat_password", "register_code"}),
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

        # Удаляем код, так как он одноразовый, а регистрация на этом моменте уже закоммичена в БД
        redis_reg_code_key = settings.redis_keys.key_reg_code(code=user_in.register_code)
        await self.redis.delete(redis_reg_code_key)

        logger.info(f"Пользователь ID: {registered_user.id}, Email: {registered_user.email} зарегистрирован")
        return registered_user


class AuthService:
    def __init__(self, uow: IUnitOfWork, redis: Redis):
        self.uow = uow
        self.redis = redis

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

    def get_auth_tokens(self, user: UserDTO) -> Token:
        """
        Получает JWT-токены для пользователя (access и refresh)

        Args:
            user - запрашивающий токен пользователь

        Returns:
            Token(access_token=AccessJWT, refresh_token=RefreshJWT, token_type="bearer")

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

    async def refresh_tokens(self, refresh_token: str) -> Token:
        """
        Метод для обработки refresh токена

        Args:
            refresh_token - refresh токен для обработки

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
            redis_blacklist_key = settings.redis_keys.key_jwt_blacklist(jti=jti)
            if await self.redis.get(redis_blacklist_key):
                raise BadCredentialsError("Токен отозван")

            user = await self.get_active_user_by_id(int(user_id))

            # Добавляем текущий refresh токен в блэклист
            await self.logout(token=refresh_token)

            return self.get_auth_tokens(user=user)

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

    async def logout(self, token: str | None) -> None:
        """
        Разлогинивает пользователя с добавлением JWT в блэклист

        Args:
            token - JWT-токен из заголовка
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
                redis_blacklist_key = settings.redis_keys.key_jwt_blacklist(jti=jti)
                await self.redis.setex(name=redis_blacklist_key, time=ttl, value="revoked")
                logger.debug(f"Токен {jti} успешно добавлен в блэклист на {ttl} сек.")

        except jwt.DecodeError:
            # Если условие не выполнилось и токен оказался абсолютно "левым"
            logger.error("Ошибка декодирования токена при попытке логаута")

            return
