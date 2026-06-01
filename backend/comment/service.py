from loguru import logger

from backend.comment.schemas import CommentCreate, CommentRead
from backend.core.constants import BusinessElementName, Action
from backend.core.uow import IUnitOfWork
from backend.exceptions import TaskDoesNotExistsError
from backend.rbac.schemas import AccessContextDTO
from backend.rbac.service import RbacService
from backend.task.schemas import TaskRead
from backend.user.schemas import UserDTO


class CommentService:
    def __init__(self, uow: IUnitOfWork, rbac_service: RbacService):
        self.uow = uow
        self.rbac = rbac_service

    async def _get_task_by_id(self, task_id) -> TaskRead:
        """
        Вспомогательный метод для поиска задачи по ID

        Args:
            task_id - ID искомой задачи

        Returns:
            Модель задачи

        Raises:
            TaskDoesNotExistsError - если задача не найдена
        """
        task = await self.uow.tasks.get_task_by_id(task_id)
        if not task:
            raise TaskDoesNotExistsError("Задача не найдена.")
        return task

    async def add_comment(
        self, task_id: int, user: UserDTO, comment_in: CommentCreate
    ) -> CommentRead:
        """
        Добавляет комментарий с проверкой прав

        Args:
            task_id - ID комментируемой задачи
            user - модель пользователя, который хочет оставить коммент
            comment_in - модель коммента для дальнейшей записи

        Returns:
            Модель готового комментария
        """
        async with self.uow:
            task = await self._get_task_by_id(task_id=task_id)

            is_author = task.author_id == user.id
            is_participant = task.executor_id == user.id
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.COMMENTS,
                action=Action.CREATE,
                context=AccessContextDTO(
                    is_participant=is_participant, is_author=is_author
                ),
                error_msg="Это не ваша задача, вы не можете ее комментировать",
            )

            new_comment = await self.uow.comments.create_comment(
                task_id=task_id, author_id=user.id, text=comment_in.text
            )

            await self.uow.commit()

        logger.success(
            f"Пользователь {user.email} оставил комментарий к задаче ID {task_id}"
        )
        return new_comment

    async def get_task_comments(self, task_id: int, user: UserDTO) -> list[CommentRead]:
        """
        Получает список всех комментариев к задаче

        Args:
            task_id - ID задачи с комментариями
            user - запрашивающий пользователь (для проверки прав)

        Returns:
            Список комментариев
        """
        async with self.uow:
            task = await self._get_task_by_id(task_id=task_id)

            is_author = task.author_id == user.id
            is_participant = task.executor_id == user.id
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.COMMENTS,
                action=Action.READ,
                context=AccessContextDTO(
                    is_participant=is_participant, is_author=is_author
                ),
                error_msg="Вы не являетесь участником задачи, комментарии недоступны.",
            )

            return await self.uow.comments.get_comments_by_task_id(task_id)
