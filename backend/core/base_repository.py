from typing import TypeVar, Generic, Any
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")
DTOType = TypeVar("DTOType", bound=BaseModel)


class BaseRepository(Generic[ModelType, DTOType]):
    def __init__(
        self, model: type[ModelType], dto: type[DTOType], session: AsyncSession
    ):
        self.model = model
        self.dto = dto
        self.session = session

    async def _get_instance(self, obj_id: int) -> ModelType | None:
        """Скрытый хелпер: возвращает SQLAlchemy-модель для внутренних операций"""
        stmt = select(self.model).where(self.model.id == obj_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, obj_id: int) -> DTOType | None:
        obj = await self._get_instance(obj_id=obj_id)
        return self.dto.model_validate(obj) if obj else None

    async def create(self, **kwargs) -> DTOType:
        instance = self.model(**kwargs)
        self.session.add(instance=instance)
        await self.session.flush()

        return self.dto.model_validate(obj=instance)

    async def update(self, obj_id: int, update_data: dict[str, Any]) -> DTOType | None:
        instance = await self._get_instance(obj_id=obj_id)

        if not instance:
            return None

        for key, value in update_data.items():
            setattr(instance, key, value)

        self.session.add(instance=instance)
        await self.session.flush()

        return self.dto.model_validate(obj=instance)

    async def delete(self, obj_id: int) -> None:
        instance = await self._get_instance(obj_id=obj_id)

        if not instance:
            return

        await self.session.delete(instance=instance)
        await self.session.flush()

    async def get_paginated(
        self, offset: int, limit: int, **filters
    ) -> tuple[list[DTOType], int]:
        """Универсальная пагинация с возвратом DTO и общего количества"""
        # Считаем тотал
        count_stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        total = await self.session.scalar(count_stmt) or 0

        # Достаем данные
        stmt = select(self.model).filter_by(**filters).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        items = result.scalars().all()

        # Мапим в DTO прямо перед отдачей
        dtos = [self.dto.model_validate(item) for item in items]
        return dtos, total
