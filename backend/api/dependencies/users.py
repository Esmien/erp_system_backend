from typing import Annotated

from fastapi import Depends, Body

from backend.api.dependencies.uow import UowDepends
from backend.rbac.service import RbacService
from backend.user.schemas import UserUpdate
from backend.user.service import UserService


def get_user_service(uow: UowDepends) -> UserService:
    """Провайдер сервиса пользователей для инъекции в Annotated"""
    rbac = RbacService(uow=uow)
    return UserService(uow=uow, rbac_service=rbac)


# Готовые DI для использования в роутерах
UserServiceDepends = Annotated[UserService, Depends(get_user_service)]
UserUpdateBody = Annotated[UserUpdate, Body()]
