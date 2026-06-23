from loguru import logger

from backend.api.dependencies.pagination import Page, PaginationParams
from backend.comment.repository import CommentRepository
from backend.comment.schemas import CommentCreate, CommentRead
from backend.core.base_service import BaseService
from backend.core.enums import Action, BusinessElementName
from backend.exceptions import CommentDoesNotExistsError, TaskDoesNotExistError
from backend.rbac.schemas import AccessContextDTO
from backend.task.schemas import TaskRead
from backend.user.schemas import UserDTO


class CommentService(BaseService[CommentRead]):
    @property
    def repository(self) -> CommentRepository:
        return self.uow.comments

    @property
    def business_element(self) -> BusinessElementName:
        return BusinessElementName.COMMENTS

    @property
    def not_found_exception(self) -> Exception:
        return CommentDoesNotExistsError("Комментарий не найден.")

    def build_abac_context(self, obj: CommentRead, user: UserDTO) -> AccessContextDTO:
        return AccessContextDTO(is_author=obj.author_id == user.id, is_participant=False)

    async def _get_task(self, task_id: int) -> TaskRead:
        """Вспомогательный метод для получения задачи"""
        task: TaskRead | None = await self.uow.tasks.get_by_id(obj_id=task_id)
        if not task:
            raise TaskDoesNotExistError("Задача не найдена.")

        return task

    async def add_comment(self, task_id: int, user: UserDTO, comment_in: CommentCreate) -> CommentRead:
        """
        Добавляет комментарий с проверкой прав

        Args:
            task_id - ID комментируемой задачи
            user - модель пользователя, который хочет оставить коммент
            comment_in - модель коммента для дальнейшей записи

        Returns:
            Модель готового комментария
        """
        task = await self._get_task(task_id=task_id)

        # Проверяем права на добавление комментария
        task_context = AccessContextDTO(
            is_author=task.author_id == user.id,
            is_participant=(task.author_id == user.id) or (task.executor_id == user.id),
        )
        await self.rbac.enforce_permission(
            user=user,
            business_element_name=BusinessElementName.COMMENTS,
            action=Action.CREATE,
            context=task_context,
            error_msg="Вы не можете оставлять комментарии к этой задаче",
        )

        # Если проверка выше прошла успешно - создаем комментарий
        new_comment = await self.repository.create(task_id=task_id, author_id=user.id, text=comment_in.text)

        await self.uow.commit()

        logger.info(f"Пользователь {user.email} оставил комментарий к задаче ID {task_id}")
        return new_comment

    async def get_task_comments(self, task_id: int, user: UserDTO, params: PaginationParams) -> Page[CommentRead]:
        """
        Получает список всех комментариев к задаче

        Args:
            task_id - ID задачи с комментариями
            user - запрашивающий пользователь (для проверки прав)
            params - параметры пагинации

        Returns:
            Объект страницы (Page), содержащий список комментариев и метаданные пагинации
        """
        task = await self._get_task(task_id=task_id)

        task_context = AccessContextDTO(
            is_author=task.author_id == user.id,
            is_participant=(task.author_id == user.id) or (task.executor_id == user.id),
        )
        await self.rbac.enforce_permission(
            user=user,
            business_element_name=BusinessElementName.TASKS,
            action=Action.READ,
            context=task_context,
            error_msg="Вы не являетесь участником задачи, комментарии недоступны.",
        )

        # Получаем комментарии с лимитами
        comments, total = await self.repository.get_comments_by_task_id(
            task_id=task_id, offset=params.offset, limit=params.limit
        )

        return Page.create(items=comments, total=total, params=params)
