from typing import Annotated

from fastapi import Depends

from backend.api.dependencies.redis import RedisDepends
from backend.api.dependencies.uow import UowDepends
from backend.rbac.api.rbac_dependencies import RbacServiceDepends
from backend.user.service import AuthService, RegisterService


def get_auth_service(uow: UowDepends, redis: RedisDepends) -> AuthService:
    """Провайдер сервиса аутентификации для инъекции в Annotated"""
    return AuthService(uow=uow, redis=redis)


def get_register_service(uow: UowDepends, redis: RedisDepends, rbac: RbacServiceDepends) -> RegisterService:
    """Провайдер сервиса регистрации для инъекции в Annotated"""
    return RegisterService(uow=uow, redis=redis, rbac_service=rbac)


# Готовые DI для использования в роутерах
AuthServiceDepends = Annotated[AuthService, Depends(get_auth_service)]
RegisterServiceDepends = Annotated[RegisterService, Depends(get_register_service)]
