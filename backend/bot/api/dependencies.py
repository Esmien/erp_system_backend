from typing import Annotated

from fastapi import Depends, Header

from backend.api.dependencies.redis import RedisDepends
from backend.api.dependencies.uow import UowDepends
from backend.bot.service import BotAuthService
from backend.user.service import AuthService


def get_bot_auth_service(uow: UowDepends, redis: RedisDepends) -> BotAuthService:
    """Провайдер сервиса аутентификации для инъекции в Annotated"""
    api_auth_service = AuthService(uow=uow, redis=redis)
    return BotAuthService(uow=uow, api_auth_service=api_auth_service, redis=redis)


BotAuthServiceDepends = Annotated[BotAuthService, Depends(get_bot_auth_service)]
BotSecretHeader = Annotated[str, Header(alias="x-bot-secret-token", description="Системный токен бота")]
