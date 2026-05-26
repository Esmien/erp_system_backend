from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from backend.api.dependencies.uow import UowDepends
from backend.user.service import AuthService, RegisterService


async def get_auth_service(uow: UowDepends) -> AuthService:
    """Провайдер сервиса аутентификации для инъекции в Annotated"""
    return AuthService(uow=uow)


async def get_register_service(uow: UowDepends) -> RegisterService:
    """Провайдер сервиса регистрации для инъекции в Annotated"""
    return RegisterService(uow=uow)


# Готовые DI для использования в роутерах
AuthFormDepends = Annotated[OAuth2PasswordRequestForm, Depends()]
AuthServiceDepends = Annotated[AuthService, Depends(get_auth_service)]
RegisterServiceDepends = Annotated[RegisterService, Depends(get_register_service)]