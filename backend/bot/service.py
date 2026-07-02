from loguru import logger
from redis.asyncio import Redis

from backend.core.config import settings
from backend.core.uow import IUnitOfWork
from backend.exceptions import BadCredentialsError, UnexpectedError, UserNotActiveError
from backend.user.schemas import UserDTO
from backend.user.service import AuthService


class BotAuthService:
    def __init__(self, uow: IUnitOfWork, api_auth_service: AuthService, redis: Redis):
        self.uow = uow
        self.api_auth_service = api_auth_service
        self.redis = redis

    async def authenticate_by_telegram(self, tg_id: int) -> UserDTO:
        """
        Тихая авторизация по Telegram ID

        Args:
            tg_id - Telegram ID пользователя

        Returns:
            Модель зарегистрированного и активного пользователя
        """
        user = await self.uow.auth.get_user(tg_id=tg_id)

        if not user:
            logger.info(f"Пользователь с Telegram ID {tg_id} не найден.")
            raise BadCredentialsError("Telegram аккаунт не привязан")

        if not user.is_active:
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
        user = await self.api_auth_service.check_users_creds(email=email, password=password)

        if getattr(user, "tg_id", None):
            logger.warning(f"У пользователя {email} уже привязан Telegram. TgID перезаписан на {tg_id}.")

        updated_user = await self.uow.users.update_user(user_id=user.id, update_dict={"tg_id": tg_id})

        if not updated_user:
            raise UnexpectedError("Неожиданная ошибка при привязке TelegramID к пользователю")

        await self.uow.commit()
        logger.info(f"Пользователь {user.email} успешно привязал Telegram ID: {tg_id}")

        return updated_user

    async def unlink_telegram_account(self, system_secret_key: str, tg_id: int) -> None:
        """
        Отвязывает TelegramID пользователя от учетной записи в БД

        Args:
            system_secret_key: системный секретный ключ
            tg_id: TelegramID отвязывающегося пользователя
        """
        expected_redis_key = settings.redis_keys.KEY_OF_SYSTEM_TOKEN
        # Читаем ожидаемый ключ из Redis
        expected_secret = await self.redis.get(expected_redis_key)

        # Если ключа в базе нет (бот еще ни разу не запускался) или они не совпадают
        if not expected_secret or system_secret_key != expected_secret:
            logger.warning(
                f"Попытка S2S запроса с невалидным ключом. Передан: {system_secret_key}\n"
                f"expected_secret: {expected_secret}\n"
                f"bot_secret_key: {system_secret_key}"
            )
            raise BadCredentialsError("Невалидный системный ключ")

        await self.uow.users.update_user(tg_id=tg_id, update_dict={"tg_id": None})
        await self.uow.commit()
        logger.info(f"TelegramID {tg_id} успешно отвязан от аккаунта пользователя")
