from typing import Annotated

from fastapi import Depends

from backend.core.uow import IUnitOfWork, UnitOfWork


async def get_uow() -> IUnitOfWork:
    """Провайдер UnitOfWork для инъекции зависимостей"""
    return UnitOfWork()


UowDepends = Annotated[IUnitOfWork, Depends(get_uow)]
