from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from backend.core.uow import IUnitOfWork, UnitOfWork


async def get_uow() -> AsyncGenerator[IUnitOfWork]:
    """Провайдер UnitOfWork для инъекции зависимостей"""
    uow = UnitOfWork()
    async with uow:
        yield uow


UowDepends = Annotated[IUnitOfWork, Depends(get_uow)]
