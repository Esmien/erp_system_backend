from typing import Any

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

    async def get_all_tasks(self) -> list[TaskRead]:
        stmt = select(Task)
        result = await self.session.execute(statement=stmt)

        return [TaskRead.model_validate(task) for task in result.scalars().all()]

    async def get_task_by_id(self, task_id: int) -> TaskRead | None:
        """
        Получает модель задачи по её ID

        Args:
            task_id - ID искомой задачи

        Returns:
            Найденная модель задачи или None, если ен нашлась
        """
        task = await self._get_task_model_by_id(task_id=task_id)
        return TaskRead.model_validate(task) if task else None

    async def create_task(self, task_in: TaskCreate, author_id: int) -> TaskRead:
        """
        Создает новую задачу в БД.

        Args:
            task_in - модель задачи для создания
            author_id - ID автора задачи

        Returns:
            Модель созданной задачи
        """
        new_task = Task(**task_in.model_dump(exclude_none=True), author_id=author_id)
        self.session.add(instance=new_task)
        await self.session.flush()

        return TaskRead.model_validate(new_task)

    async def update_task(
        self, task_id: int, update_data: dict[str, Any]
    ) -> TaskRead | None:
        """
        Обновляет существующую задачу

        Args:
            task_id - ID задачи для обновления
            update_data - данные для обновления

        Returns:
            Модель обновленной задачи или None, если ID задачи не найден
        """
        task = await self._get_task_model_by_id(task_id=task_id)

        if not task:
            return None

        # Записываем обновленные поля задачи в модель
        for key, value in update_data.items():
            setattr(task, key, value)

        self.session.add(instance=task)
        await self.session.flush()

        return TaskRead.model_validate(task)

    async def delete_task(self, task_id: int) -> None:
        """
        Удаляет задачу из БД

        Args:
            task_id - ID удаляемой задачи
        """
        task = await self._get_task_model_by_id(task_id=task_id)

        if not task:
            return

        await self.session.delete(task)
        await self.session.flush()
