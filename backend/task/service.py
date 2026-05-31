from loguru import logger

from backend.core.uow import IUnitOfWork
from backend.core.constants import RoleName, TaskStatus
from backend.task.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskRead,
    TaskChangeStatus,
)
from backend.user.schemas import UserDTO
from backend.exceptions import (
    AccessDeniedError,
    TaskDoesNotExistsError,
    UserDoesNotExistsError,
    TeamDoesNotExistsError,
)


class TaskService:
    TASK_NOT_FOUND = "Задача не найдена."

    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    @staticmethod
    def _check_user_is_manager_or_author(task: TaskRead, user: UserDTO) -> None:
        """
        Вспомогательный метод для проверки прав.
        Разрешает доступ, если пользователь - админ, менеджер или создатель задачи.
        """

        # Проверка ролей и авторства
        is_manager_or_admin = user.role.name in (RoleName.ADMIN, RoleName.MANAGER)
        is_author = task.author_id == user.id

        if not (is_manager_or_admin or is_author):
            logger.warning(
                f"Отказ в доступе. Пользователь {user.email} пытался изменить задачу ID {task.id}"
            )
            raise AccessDeniedError(
                "У вас нет прав на редактирование/удаление этой задачи"
            )

    async def get_task(self, task_id: int) -> TaskRead:
        """
        Получает задачу по ID

        Args:
            task_id - ID искомой задачи

        Returns:
            Модель найденной задачи

        Raises:
            TaskDoesNotExists - если задача не нашлась
        """
        async with self.uow:
            task = await self.uow.tasks.get_task_by_id(task_id)

        if not task:
            logger.info(f"Задача с ID: {task_id} не найдена.")
            raise TaskDoesNotExistsError(self.TASK_NOT_FOUND)

        return task

    async def get_filtered_tasks(
        self, user: UserDTO, scope: str, task_status: TaskStatus | None
    ) -> list[TaskRead]:
        user_id_filter = None
        team_id_filter = None

        if scope == "my":
            user_id_filter = user.id
        elif scope == "team":
            if not user.team_id:
                raise TeamDoesNotExistsError(
                    f"Пользователь {user.email} не состоит в команде"
                )

            team_id_filter = user.team_id
        elif scope == "all":
            if user.role.name not in (RoleName.ADMIN, RoleName.MANAGER):
                raise AccessDeniedError("Недостаточно прав для просмотра всех задач")

        async with self.uow:
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
        """
        async with self.uow:
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
        """
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            # Если обновлять нечего, просто возвращаем текущую задачу
            return await self.get_task(task_id)

        async with self.uow:
            task = await self.uow.tasks.get_task_by_id(task_id)
            if not task:
                raise TaskDoesNotExistsError(self.TASK_NOT_FOUND)

            # Проверка прав: руководитель или автор
            self._check_user_is_manager_or_author(task=task, user=user)

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
        async with self.uow:
            task = await self.uow.tasks.get_task_by_id(task_id)
            if not task:
                raise TaskDoesNotExistsError(self.TASK_NOT_FOUND)

            is_manager_or_admin = user.role.name in (RoleName.ADMIN, RoleName.MANAGER)
            is_allowed = (
                (task.executor_id == user.id)
                or (task.author_id == user.id)
                or is_manager_or_admin
            )

            if not is_allowed:
                logger.warning(
                    f"Попытка изменить статус задачи {task.title} без прав (User: {user.email})"
                )
                raise AccessDeniedError("Недостаточно прав для изменения статуса")

            updated_task = await self.uow.tasks.update_task(
                task_id=task_id, update_data=new_status.model_dump()
            )

            # Если что-то пошло не так на стороне репозитория
            if not updated_task:
                raise TaskDoesNotExistsError(self.TASK_NOT_FOUND)

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
            TaskDoesNotExistsError - если задача не нашлась
        """
        async with self.uow:
            task = await self.uow.tasks.get_task_by_id(task_id)
            if not task:
                raise TaskDoesNotExistsError(self.TASK_NOT_FOUND)

            # Проверка прав: руководитель или автор
            self._check_user_is_manager_or_author(task=task, user=user)

            await self.uow.tasks.delete_task(task_id=task_id)
            await self.uow.commit()

        logger.success(f"Задача ID {task_id} удалена пользователем {user.email}")
