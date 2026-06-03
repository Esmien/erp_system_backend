from typing import Literal

from loguru import logger

from backend.core.uow import IUnitOfWork
from backend.core.constants import (
    TaskStatus,
    TASK_NOT_FOUND,
    BusinessElementName,
    Action,
)
from backend.rbac.schemas import AccessContextDTO
from backend.rbac.service import RbacService
from backend.task.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskRead,
    TaskChangeStatus,
)
from backend.user.schemas import UserDTO
from backend.exceptions import (
    TaskDoesNotExistsError,
    UserDoesNotExistsError,
    TeamDoesNotExistsError,
)


class TaskService:
    def __init__(self, uow: IUnitOfWork, rbac_service: RbacService):
        self.uow = uow
        self.rbac = rbac_service

    @staticmethod
    def _build_task_context(task: TaskRead, user: UserDTO) -> AccessContextDTO:
        """Собирает ABAC-контекст для проверки прав"""
        return AccessContextDTO(
            is_author=task.author_id == user.id,
            is_participant=(task.author_id == user.id) or (task.executor_id == user.id),
        )

    async def _get_task_by_id(self, task_id: int) -> TaskRead:
        """
        Вспомогательный метод для быстрого получения задачи по ее ID

        Args:
            task_id - ID задачи

        Returns:
            Найденная задача

        Raises:
            TaskDoesNotExistsError - если задача не нашлась
        """
        task = await self.uow.tasks.get_task_by_id(task_id=task_id)
        if not task:
            raise TaskDoesNotExistsError(TASK_NOT_FOUND)
        return task

    async def get_task(self, task_id: int, user: UserDTO) -> TaskRead:
        """
        Получает задачу по ID с проверкой прав

        Args:
            task_id - ID искомой задачи
            user - пользователь, который запрашивает задачу

        Returns:
            Модель найденной задачи

        Raises:
            TaskDoesNotExists - если задача не нашлась
            AccessDeniedError - если нет прав на просмотр задачи
        """
        async with self.uow:
            task = await self._get_task_by_id(
                task_id=task_id
            )  # Raises TaskDoesNotExists

            context = self._build_task_context(task=task, user=user)
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.TASKS,
                action=Action.READ,
                context=context,
                error_msg="Нет прав на просмотр этой задачи",
            )

            return task

    async def get_filtered_tasks(
        self,
        user: UserDTO,
        scope: Literal["my", "team", "all"],
        task_status: TaskStatus | None,
    ) -> list[TaskRead]:
        """
        Получает отфильтрованный по критериям список задач

        Args:
            user - пользователь, который получает данные
            scope - ширина поиска (свои -> командные -> все) задач
            task_status - статус задачи (для фильтров)

        Returns:
            Список задач после фильтрации

        Raises:
            AccessDeniedError - если нет доступа к общему скоупу (нет прав на просмотр "all")
            TeamDoesNotExistsError - если пользователь не состоит в команде, но запрашивает командные задачи
        """
        context = AccessContextDTO(is_participant=scope in ["my", "team"])

        user_id_filter = user.id if scope == "my" else None
        team_id_filter = None

        if scope == "team":
            if not user.team_id:
                raise TeamDoesNotExistsError(
                    f"Пользователь {user.email} не состоит в команде"
                )
            team_id_filter = user.team_id

        async with self.uow:
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.TASKS,
                action=Action.READ,
                context=context,
                error_msg="Недостаточно прав для просмотра всех задач",
            )

            tasks = await self.uow.tasks.get_tasks_with_filters(
                user_id=user_id_filter, team_id=team_id_filter, task_status=task_status
            )

        if not tasks:
            logger.info("Задачи не найдены.")

        return tasks

    async def create_task(self, task_in: TaskCreate, author: UserDTO) -> TaskRead:
        """
        Создает новую задачу

        Args:
            task_in - модель задачи для создания
            author - модель автора задачи

        Returns:
            Модель созданной задачи

        Raises:
            AccessDeniedError - если нет прав для создания задачи
        """
        async with self.uow:
            await self.rbac.enforce_permission(
                user=author,
                business_element_name=BusinessElementName.TASKS,
                action=Action.CREATE,
                error_msg="Недостаточно прав для создания задачи",
            )

            new_task = await self.uow.tasks.create_task(
                task_in=task_in, author_id=author.id
            )
            await self.uow.commit()

        logger.success(
            f"Задача '{new_task.title}' успешно создана пользователем {author.email}"
        )
        return new_task

    async def update_task(
        self, task_id: int, update_data: TaskUpdate, user: UserDTO
    ) -> TaskRead:
        """
        Обновляет задачу с проверкой прав

        Args:
            task_id - ID задачи для обновления
            update_data - модель с данными для обновления
            user - модель пользователя, который пытается обновить задачу

        Returns:
            Обновленная модель задачи

        Raises:
            TaskDoesNotExists - если задача не нашлась
            UserDoesNotExistsError - если назначаемый исполнитель не существует
            AccessDeniedError - если нет прав на обновление задачи
        """
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            # Если обновлять нечего, просто возвращаем текущую задачу
            return await self.get_task(task_id=task_id, user=user)

        async with self.uow:
            task = await self._get_task_by_id(task_id=task_id)

            context = self._build_task_context(user=user, task=task)
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.TASKS,
                action=Action.UPDATE,
                context=context,
                error_msg="У вас нет прав для редактирования этой задачи",
            )

            executor_id = update_dict.get("executor_id")
            if executor_id is not None:
                executor = await self.uow.auth.get_user_and_role_by_user_id(executor_id)
                if not executor:
                    raise UserDoesNotExistsError(
                        "Попытка назначить несуществующего исполнителя"
                    )

            updated_task = await self.uow.tasks.update_task(
                task_id=task_id, update_data=update_dict
            )
            # Если что-то пошло не так на стороне репозитория
            if not updated_task:
                raise TaskDoesNotExistsError

            await self.uow.commit()

        logger.success(f"Задача ID {task_id} обновлена пользователем {user.email}")
        return updated_task

    async def change_status(
        self, task_id: int, new_status: TaskChangeStatus, user: UserDTO
    ) -> TaskRead:
        """
        Меняет статус задачи (Task.status)

        Args:
            task_id - ID редактируемой задачи
            new_status - новый статус для задачи
            user - пользователь, меняющий статус

        Returns:
            Задача с обновленным статусом

        Raises:
            AccessDeniedError - если нет прав на изменение статуса
            TaskDoesNotExistsError - если задача не найдена
        """
        async with self.uow:
            task = await self._get_task_by_id(task_id=task_id)

            context = self._build_task_context(user=user, task=task)
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.TASKS,
                action=Action.CHANGE_STATUS,
                context=context,
                error_msg="Недостаточно прав для изменения статуса",
            )

            updated_task = await self.uow.tasks.update_task(
                task_id=task_id, update_data=new_status.model_dump()
            )

            # Если что-то пошло не так на стороне репозитория
            if not updated_task:
                raise TaskDoesNotExistsError(TASK_NOT_FOUND)

            await self.uow.commit()

        logger.success(f"Задаче ID {task_id} присвоен статус {updated_task.status}")
        return updated_task

    async def delete_task(self, task_id: int, user: UserDTO) -> None:
        """
        Удаляет задачу с проверкой прав

        Args:
            task_id - ID задачи для удаления
            user - пользователь, который удаляет задачу

        Raises:
            AccessDeniedError - если нет прав на удаление
            TaskDoesNotExistsError - если задача не нашлась
        """
        async with self.uow:
            task = await self._get_task_by_id(task_id=task_id)

            context = self._build_task_context(user=user, task=task)
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.TASKS,
                action=Action.DELETE,
                context=context,
                error_msg="Недостаточно прав для удаления этой задачи",
            )

            await self.uow.tasks.delete_task(task_id=task_id)
            await self.uow.commit()

        logger.success(f"Задача ID {task_id} удалена пользователем {user.email}")
