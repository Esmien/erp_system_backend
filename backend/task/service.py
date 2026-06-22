from typing import Literal

from loguru import logger

from backend.api.dependencies.pagination import Page, PaginationParams
from backend.core.base_service import BaseService
from backend.core.enums import (
    TASK_NOT_FOUND,
    Action,
    BusinessElementName,
    TaskStatus,
)
from backend.exceptions import (
    TaskDoesNotExistError,
    TeamDoesNotExistError,
    UserDoesNotExistError,
)
from backend.rbac.schemas import AccessContextDTO
from backend.task.repository import TaskRepository
from backend.task.schemas import (
    TaskChangeStatus,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from backend.user.schemas import UserDTO


class TaskService(BaseService[TaskRead]):
    @property
    def repository(self) -> TaskRepository:
        return self.uow.tasks

    @property
    def business_element(self) -> BusinessElementName:
        return BusinessElementName.TASKS

    @property
    def not_found_exception(self) -> Exception:
        return TaskDoesNotExistError("Задача не найдена.")

    def build_abac_context(self, obj: TaskRead, user: UserDTO) -> AccessContextDTO:
        return AccessContextDTO(
            is_author=obj.author_id == user.id,
            is_participant=(obj.author_id == user.id) or (obj.executor_id == user.id),
        )

    async def get_filtered_tasks(
        self,
        user: UserDTO,
        scope: Literal["my", "team", "all"],
        task_status: TaskStatus | None,
        params: PaginationParams,  # <-- Добавили параметры пагинации
    ) -> Page[TaskRead]:
        """
        Получает отфильтрованный по критериям список задач

        Args:
            user - пользователь, который получает данные
            scope - ширина поиска (свои -> командные -> все) задач
            task_status - статус задачи (для фильтров)

        Returns:
            Объект страницы (Page), содержащий список комментариев и метаданные пагинации

        Raises:
            AccessDeniedError - если нет доступа к общему скоупу (нет прав на просмотр "all")
            TeamDoesNotExistsError - если пользователь не состоит в команде, но запрашивает командные задачи
        """
        # Пользователь без прав типа ALL на чтение задач
        # может получить только свои таски или таски группы
        context = AccessContextDTO(is_participant=scope in ["my", "team"])

        # Собираем последовательно фильтры от меньшего к большему
        user_id_filter = user.id if scope == "my" else None
        team_id_filter = None

        if scope == "team":
            if not user.team_id:
                raise TeamDoesNotExistError(f"Пользователь {user.email} не состоит в команде")
            team_id_filter = user.team_id

        async with self.uow:
            # Проверяем права
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.TASKS,
                action=Action.READ,
                context=context,
                error_msg="Недостаточно прав для просмотра всех задач",
            )

            # Собираем отфильтрованные по скоупам таски
            tasks, total = await self.repository.get_tasks_with_filters(
                offset=params.offset,
                limit=params.limit,
                user_id=user_id_filter,
                team_id=team_id_filter,
                task_status=task_status,
            )

        if not tasks:
            logger.info("Задачи не найдены.")

        return Page.create(items=tasks, total=total, params=params)

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
            await self.check_permissions(
                user=author,
                action=Action.CREATE,
                error_msg="Вы не можете создавать задачи",
            )

            new_task = await self.repository.create(**task_in.model_dump(), author_id=author.id)
            await self.uow.commit()

        logger.info(f"Задача '{new_task.title}' успешно создана пользователем {author.email}")
        return new_task

    async def update_task(self, task_id: int, update_data: TaskUpdate, user: UserDTO) -> TaskRead:
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
            return await self.get(obj_id=task_id, user=user)

        async with self.uow:
            task = await self.get_or_raise(obj_id=task_id)

            await self.check_permissions(
                user=user,
                action=Action.UPDATE,
                obj=task,
                error_msg="Вы не можете редактировать эту задачу",
            )

            # Проверяем существование пользователя для назначения исполнителем
            executor_id = update_dict.get("executor_id")
            if executor_id is not None:
                executor = await self.uow.auth.get_user_and_role_by_user_id(executor_id)
                if not executor:
                    raise UserDoesNotExistError("Попытка назначить несуществующего исполнителя")

            updated_task = await self.repository.update(obj_id=task_id, update_data=update_dict)
            # Если что-то пошло не так на стороне репозитория
            if not updated_task:
                raise self.not_found_exception

            await self.uow.commit()

        logger.info(f"Задача ID {task_id} обновлена пользователем {user.email}")
        return updated_task

    async def change_status(self, task_id: int, new_status: TaskChangeStatus, user: UserDTO) -> TaskRead:
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
            task = await self.get_or_raise(obj_id=task_id)

            await self.check_permissions(
                user=user,
                action=Action.CHANGE_STATUS,
                obj=task,
                error_msg="Вы не можете изменить статус этой задачи",
            )

            updated_task = await self.repository.update(obj_id=task_id, update_data=new_status.model_dump())

            # Если что-то пошло не так на стороне репозитория
            if not updated_task:
                raise TaskDoesNotExistError(TASK_NOT_FOUND)

            await self.uow.commit()

        logger.info(f"Задаче ID {task_id} присвоен статус {updated_task.status}")
        return updated_task
