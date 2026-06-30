from typing import Annotated

from fastapi import Depends, Header

from backend.api.dependencies.uow import UowDepends
from backend.user.service import AuthService, RegisterService


def get_auth_service(uow: UowDepends) -> AuthService:
    """Провайдер сервиса аутентификации для инъекции в Annotated"""
    return AuthService(uow=uow)


def get_register_service(uow: UowDepends) -> RegisterService:
    """Провайдер сервиса регистрации для инъекции в Annotated"""
    return RegisterService(uow=uow)


# Готовые DI для использования в роутерах
AuthServiceDepends = Annotated[AuthService, Depends(get_auth_service)]
RegisterServiceDepends = Annotated[RegisterService, Depends(get_register_service)]
BotSecretHeader = Annotated[str, Header(alias="x-bot-secret-token", description="Системный токен бота")]
