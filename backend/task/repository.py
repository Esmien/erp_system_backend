from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.task.models import Task
from backend.task.schemas import TaskCreate, TaskRead


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_task_model_by_id(self, task_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(statement=stmt)
        task = result.scalar_one_or_none()

        return task

    async def get_task_by_id(self, task_id: int) -> TaskRead | None:
        """
        Получает модель задачи по её ID.
        """
        task = await self._get_task_model_by_id(task_id=task_id)
        return TaskRead.model_validate(task) if task else None

    async def create_task(self, task_in: TaskCreate, author_id: int) -> TaskRead:
        """
        Создает новую задачу в БД.
        """
        new_task = Task(**task_in.model_dump(), author_id=author_id)
        self.session.add(instance=new_task)
        await self.session.commit()
        await self.session.refresh(instance=new_task)

        return TaskRead.model_validate(new_task)

    async def update_task(
        self, task_id: int, update_data: dict[str, Any]
    ) -> TaskRead | None:
        """
        Обновляет существующую задачу.
        """
        task = await self._get_task_model_by_id(task_id=task_id)

        if not task:
            return None

        for key, value in update_data.items():
            setattr(task, key, value)

        self.session.add(instance=task)
        await self.session.commit()
        await self.session.refresh(instance=task)
        return TaskRead.model_validate(task)

    async def delete_task(self, task_id: int) -> None:
        """
        Удаляет задачу из БД (hard delete).
        """
        task = await self._get_task_model_by_id(task_id=task_id)
        if not task:
            logger.warning(f"Задача с ID: {task_id} не найдена.")
        await self.session.delete(task)
        await self.session.commit()

        logger.success(f"Задача {task.title} успешно удалена.")
