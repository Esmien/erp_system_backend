from typing import Annotated

from fastapi import Depends

from backend.api.dependencies.uow import UowDepends
from backend.rbac.service import RbacService


async def get_rbac_service(uow: UowDepends) -> RbacService:
    """Провайдер сервиса RBAC для инъекции в Annotated"""
    return RbacService(uow=uow)


# Готовая DI для использования в роутерах
RbacServiceDepends = Annotated[RbacService, Depends(get_rbac_service)]