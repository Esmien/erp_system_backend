from typing import Annotated

from fastapi import Depends, Body

from backend.api.dependencies.rbac import RbacServiceDepends
from backend.api.dependencies.uow import UowDepends
from backend.user.schemas import UserUpdate
from backend.user.service import UserService


def get_user_service(uow: UowDepends, rbac: RbacServiceDepends) -> UserService:
    """Провайдер сервиса пользователей для инъекции в Annotated"""
    return UserService(uow=uow, rbac_service=rbac)


# Готовые DI для использования в роутерах
UserServiceDepends = Annotated[UserService, Depends(get_user_service)]
UserUpdateBody = Annotated[UserUpdate, Body()]
