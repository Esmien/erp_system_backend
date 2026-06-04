from backend.core.constants import (
    BusinessElementName,
    Action,
    TASK_NOT_FOUND,
    TaskStatus,
)
from backend.core.uow import IUnitOfWork
from backend.exceptions import (
    TaskDoesNotExistsError,
    TaskAlreadyEvaluatedError,
    TaskDoesNotCompletedError,
)
from backend.evaluation.schemas import (
    EvaluationCreate,
    EvaluationRead,
    EvaluationCreateDTO,
    UserStatisticsRead,
)
from backend.rbac.schemas import AccessContextDTO
from backend.rbac.service import RbacService
from backend.user.schemas import UserDTO


class EvaluationService:
    def __init__(self, uow: IUnitOfWork, rbac_service: RbacService):
        self.uow = uow
        self.rbac = rbac_service

    async def evaluate_task(
        self, task_id: int, evaluation_in: EvaluationCreate, user: UserDTO
    ) -> EvaluationRead:
        """
        Выставляет оценку к задаче

        Args:
            task_id - задача для оценки
            evaluation_in - оценка
            user - кто ставит оценку

        Returns:
            Оценка со всеми полями

        Raises:
            AccessDeniedError - если нет прав для оценки задачи
            TaskDoesNotExistsError - если нет искомой задачи
            TaskAlreadyEvaluatedError - если оценка уже стоит
            TaskDoesNotCompletedError - если задача еще не завершена
        """
        async with self.uow:
            # Проверяем глобальные права на выставление оценок
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.EVALUATIONS,
                action=Action.CREATE,
                error_msg="Недостаточно прав для оценки задачи",
            )

            # Проверяем, существует ли задача
            task = await self.uow.tasks.get_task_by_id(task_id)
            if not task:
                raise TaskDoesNotExistsError(TASK_NOT_FOUND)

            if task.status is not TaskStatus.DONE:
                raise TaskDoesNotCompletedError("Задача еще не выполнена")

            # Проверяем, не оценена ли задача уже
            existing_eval = await self.uow.evaluations.get_by_task_id(task_id)
            if existing_eval:
                raise TaskAlreadyEvaluatedError("Эта задача уже оценена")

            # Сохраняем
            new_eval = EvaluationCreateDTO(
                value=evaluation_in.value,
                comment=evaluation_in.comment,
                task_id=task_id,
                evaluator_id=user.id,
            )
            saved_eval = await self.uow.evaluations.add(new_eval)

            await self.uow.commit()

            return saved_eval

    async def get_evaluation(
        self, task_id: int, user: UserDTO
    ) -> EvaluationRead | None:
        """
        Получает оценку к задаче

        Args:
            task_id - ID искомой задачи
            user - текущий пользователь, для проверки прав на просмотр

        Returns:
            Оценка или None, если оценки нет

        Raises:
            TaskDoesNotExistsError - если не найдена задача
            AccessDeniedError - если нет прав на просмотр оценки
        """
        async with self.uow:
            task = await self.uow.tasks.get_task_by_id(task_id)
            if not task:
                raise TaskDoesNotExistsError(TASK_NOT_FOUND)

            # Проверяем причастность юзера к задаче
            is_participant = (task.author_id == user.id) or (
                task.executor_id == user.id
            )
            context = AccessContextDTO(is_participant=is_participant)

            # Проверяем права на чтение с учетом контекста
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.EVALUATIONS,
                action=Action.READ,
                context=context,
                error_msg="У вас нет прав для просмотра этой оценки",
            )

            evaluation = await self.uow.evaluations.get_by_task_id(task_id)

            return evaluation

    async def get_my_statistics(self, user: UserDTO) -> UserStatisticsRead:
        """
        Возвращает статистику оценок текущего пользователя

        Args:
            user - текущий пользователь

        Returns:
            Статистика текущего пользователя
        """
        async with self.uow:
            return await self.uow.evaluations.get_user_statistics(user_id=user.id)
