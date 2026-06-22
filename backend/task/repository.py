from datetime import date

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.base_repository import BaseRepository
from backend.task.models import Task
from backend.task.schemas import TaskRead
from backend.user.models import User


class TaskRepository(BaseRepository[Task, TaskRead]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Task, dto=TaskRead)

    async def get_tasks_with_filters(
        self,
        offset: int,
        limit: int,
        user_id: int | None = None,
        team_id: int | None = None,
        task_status: str | None = None,
    ) -> tuple[list[TaskRead], int]:
        """
        Получает задачи по фильтрам

        Args:
            offset - смещение указателя при чтении большого количества данных
            limit - ограничение на количество выдаваемых за раз данных
            user_id - ID запрашивающего задачи пользователя
            team_id - ID команды, чьи задачи запрашиваются
            task_status - статус искомых задач

        Returns:
            Список отфильтрованных задач и их общее количество
        """
        stmt = select(Task)

        if task_status:
            stmt = stmt.where(Task.status == task_status)

        if user_id:
            stmt = stmt.where(or_(Task.author_id == user_id, Task.executor_id == user_id))
        elif team_id:
            stmt = stmt.join(User, Task.executor_id == User.id).where(User.team_id == team_id)

        return await self._paginate_statement(stmt=stmt, limit=limit, offset=offset)

    async def get_tasks_by_date_range(self, user_id: int, start_date: date, end_date: date) -> list[TaskRead]:
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
        tasks = result.scalars().all()

        return [TaskRead.model_validate(obj=task) for task in tasks]
