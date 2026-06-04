from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.evaluation.models import Evaluation
from backend.evaluation.schemas import (
    EvaluationRead,
    EvaluationCreateDTO,
    UserStatisticsRead,
)
from backend.task.models import Task


class EvaluationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, evaluation: EvaluationCreateDTO) -> EvaluationRead:
        """
        Добавляет оценку к задаче

        Args:
            evaluation - модель оценки

        Returns:
            Оценка со всеми нужными полями
        """
        new_eval = Evaluation(**evaluation.model_dump(exclude_none=True))

        self.session.add(instance=new_eval)
        await self.session.flush()
        await self.session.refresh(instance=new_eval)

        return EvaluationRead.model_validate(obj=new_eval)

    async def get_by_task_id(self, task_id: int) -> EvaluationRead | None:
        """
        Ищет оценку по ID задачи

        Args:
            task_id - ID задачи, к которой ищется оценка

        Returns:
            Оценка или None, если оценка еще не стоит
        """
        stmt = select(Evaluation).where(Evaluation.task_id == task_id)
        result = await self.session.execute(statement=stmt)
        eval_model = result.scalar_one_or_none()

        return EvaluationRead.model_validate(obj=eval_model) if eval_model else None

    async def get_user_statistics(self, user_id: int) -> UserStatisticsRead:
        """
        Считает среднюю оценку и количество оцененных задач для пользователя

        Args:
            user_id - ID пользователя для подсчета статистики

        Returns:
            Статистика пользователя
        """
        stmt = (
            select(
                func.avg(Evaluation.value).label("avg_value"),
                func.count(Evaluation.id).label("count_evals"),
            )
            .join(Task, Task.id == Evaluation.task_id)
            .where(Task.executor_id == user_id)
        )

        result = await self.session.execute(statement=stmt)
        row = result.one()

        avg_val = row.avg_value
        count_val = row.count_evals

        return UserStatisticsRead(
            average_evaluation=round(float(avg_val), 2) if avg_val else 0,
            tasks_evaluated_count=count_val if count_val else 0
        )
