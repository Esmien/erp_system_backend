from datetime import date

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.base_repository import BaseRepository
from backend.task.models import Task
from backend.task.schemas import TaskRead
from backend.user.models import User


class TaskRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Task, dto=TaskRead)

    async def get_tasks_with_filters(
        self,
        user_id: int | None = None,
        team_id: int | None = None,
        task_status: str | None = None,
    ) -> list[TaskRead]:
        stmt = select(Task)

        if task_status:
            stmt = stmt.where(Task.status == task_status)

        if user_id:
            stmt = stmt.where(
                or_(Task.author_id == user_id, Task.executor_id == user_id)
            )
        elif team_id:
            stmt = stmt.join(User, Task.executor_id == User.id).where(
                User.team_id == team_id
            )

        result = await self.session.execute(statement=stmt)

        return [TaskRead.model_validate(obj=task) for task in result.scalars().all()]

    async def get_tasks_by_date_range(
        self, user_id: int, start_date: date, end_date: date
    ) -> list[TaskRead]:
        """
        Возвращает все доступные пользователю задачи за выбранный период

        Args:
            user_id - ID запрашивающего пользователя
            start_date - начало периода
            end_date - конец периода

        Returns:
            Список отфильтрованных задач
        """
        stmt = select(Task).where(
            and_(
                or_(Task.author_id == user_id, Task.executor_id == user_id),
                Task.expire >= start_date,
                Task.expire <= end_date,
            )
        )
        result = await self.session.execute(statement=stmt)
        return [TaskRead.model_validate(obj=t) for t in result.scalars().all()]
