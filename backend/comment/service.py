from loguru import logger

from backend.comment.schemas import CommentCreate, CommentRead
from backend.core.constants import RoleName
from backend.core.uow import IUnitOfWork
from backend.exceptions import TaskDoesNotExistsError, AccessDeniedError
from backend.user.schemas import UserDTO


class CommentService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

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
            is_manager_or_admin = user.role.name in (RoleName.ADMIN, RoleName.MANAGER)
            is_allowed = (
                (task.executor_id == user.id)
                or (task.author_id == user.id)
                or is_manager_or_admin
            )

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
