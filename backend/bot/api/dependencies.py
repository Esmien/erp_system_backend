from typing import Annotated

from fastapi import Depends, Header

from backend.api.dependencies.uow import UowDepends
from backend.bot.service import BotAuthService


def get_auth_service(uow: UowDepends) -> BotAuthService:
    """Провайдер сервиса аутентификации для инъекции в Annotated"""
    return BotAuthService(uow=uow)


BotAuthServiceDepends = Annotated[BotAuthService, Depends(get_auth_service)]
BotSecretHeader = Annotated[str, Header(alias="x-bot-secret-token", description="Системный токен бота")]
