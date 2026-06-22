from typing import Any, TypeVar

from loguru import logger
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")
DTOType = TypeVar("DTOType", bound=BaseModel)


class BaseRepository[ModelType, DTOType: BaseModel]:
    def __init__(self, model: type[ModelType], dto: type[DTOType], session: AsyncSession):
        self.model = model
        self.dto = dto
        self.session = session

    async def _get_instance(self, obj_id: int) -> ModelType | None:
        """Скрытый хелпер: возвращает SQLAlchemy-модель для внутренних операций"""
        stmt = select(self.model).where(self.model.id == obj_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, obj_id: int) -> DTOType | None:
        """Возвращает найденный в БД по ID объект в виде DTO"""
        obj = await self._get_instance(obj_id=obj_id)
        return self.dto.model_validate(obj) if obj else None

    async def create(self, **kwargs) -> DTOType:
        """
        Универсальный метод для создания чего-либо в БД

        Args:
            kwargs - именованные аргументы с полями создаваемого объекта

        Returns:
            Готовый для дальнейшей обработки DTO на основе созданной в БД записи
        """
        instance = self.model(**kwargs)
        self.session.add(instance=instance)
        await self.session.flush()
        await self.session.refresh(instance=instance)

        return self.dto.model_validate(obj=instance)

    async def update(self, obj_id: int, update_data: dict[str, Any]) -> DTOType | None:
        """
        Универсальный метод для обновления записи в БД

        Args:
            obj_id - ID изменяемого объекта
            update_data - словарь с данными для обновления

        Returns:
            DTO обновленной записи или None, если запись не существует
        """
        instance = await self._get_instance(obj_id=obj_id)

        if not instance:
            return None

        # Обновляем поля ORM-модели
        for key, value in update_data.items():
            setattr(instance, key, value)

        # Записываем, получаем из БД обновленную ORM-модель, собираем DTO и отдаем наверх
        self.session.add(instance=instance)
        await self.session.flush()

        return self.dto.model_validate(obj=instance)

    async def delete(self, obj_id: int) -> None:
        """
        Универсальный метод для удаления записи из БД

        Args:
            obj_id - ID удаляемого объекта
        """
        instance = await self._get_instance(obj_id=obj_id)

        if not instance:
            return

        await self.session.delete(instance=instance)
        await self.session.flush()

    async def _paginate_statement(self, stmt: Select, offset: int, limit: int) -> tuple[list[DTOType], int]:
        """
        Универсальный обработчик пагинации для любых, даже самых сложных запросов.
        Принимает готовый Select-запрос, считает total и отдает страницу с DTO.
        """
        try:
            # Считаем общее количество записей, игнорируя сортировку (чтобы не тормозило)
            count_stmt = stmt.with_only_columns(func.count(self.model.id)).order_by(None)
            total = await self.session.scalar(count_stmt) or 0

            # Навешиваем пагинацию на исходный запрос
            paginated_stmt = stmt.offset(offset).limit(limit)
            result = await self.session.execute(paginated_stmt)

            # scalars().unique().all() нужен на случай, если в запросе есть джойны
            # один-ко-многим или selectinload, чтобы алхимия не дублировала строки
            items = result.scalars().unique().all()

            # Мапим в DTO
            dtos = [self.dto.model_validate(item) for item in items]

            return dtos, total
        except SQLAlchemyError as e:
            # Логируем контекст (на какой модели упало)
            logger.error(f"Ошибка выполнения сложного запроса пагинации для модели {self.model.__name__}: {e}")
            # Пробрасываем ошибку дальше, чтобы ее поймал наш глобальный sqlalchemy_exception_handler
            raise

    async def get_paginated(self, offset: int, limit: int, **filters) -> tuple[list[DTOType], int]:
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
