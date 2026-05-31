from loguru import logger

from backend.comment.schemas import CommentCreate, CommentRead
from backend.core.constants import RoleName
from backend.core.uow import IUnitOfWork
from backend.exceptions import TaskDoesNotExistsError, AccessDeniedError
from backend.task.schemas import TaskRead
from backend.user.schemas import UserDTO


class CommentService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    # ToDo вынести все подобные проверки на уровень БД
    @staticmethod
    async def _check_access(user: UserDTO, task: TaskRead) -> bool:
        """
        Вспомогательный метод для проверки прав на написание комментариев

        Args:
            user - модель пользователя для проверки
            task - задача, доступ к которой проверяется

        Returns:
            True, если доступ разрешен, False - если нет
        """
        is_manager_or_admin = user.role.name in (RoleName.ADMIN, RoleName.MANAGER)
        return (
            task.executor_id == user.id
            or task.author_id == user.id
            or is_manager_or_admin
        )

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
            task = await self.uow.tasks.get_task_by_id(task_id)
            if not task:
                raise TaskDoesNotExistsError("Задача не найдена.")

            # Проверка прав: админ, менеджер, автор или исполнитель
            is_allowed = await self._check_access(user=user, task=task)

            if not is_allowed:
                logger.warning(
                    f"Попытка комментирования задачи {task_id} без прав (User: {user.email})"
                )
                raise AccessDeniedError("Недостаточно прав для комментирования задачи")

            new_comment = await self.uow.comments.create_comment(
                task_id=task_id, author_id=user.id, text=comment_in.text
            )

            await self.uow.commit()

        logger.success(
            f"Пользователь {user.email} оставил комментарий к задаче ID {task_id}"
        )
        return new_comment

    async def get_task_comments(self, task_id: int, user: UserDTO) -> list[CommentRead]:
        async with self.uow:
            task = await self.uow.tasks.get_task_by_id(task_id)
            if not task:
                raise TaskDoesNotExistsError("Задача не найдена.")

            # Проверка прав доступа (те же, что и при создании)
            is_allowed = await self._check_access(user=user, task=task)

            if not is_allowed:
                raise AccessDeniedError("Недостаточно прав для просмотра комментариев")

            return await self.uow.comments.get_comments_by_task_id(task_id)
