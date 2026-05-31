from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.comment.models import Comment
from backend.comment.schemas import CommentRead


class CommentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_comment(
        self, task_id: int, author_id: int, text: str
    ) -> CommentRead:
        """
        Создает комментарий к задаче

        Args:
            task_id - ID задачи к которой пишется комментарий
            author_id - ID автора
            text - содержание комментария

        Returns:
            Модель комментария со всеми метаданными
        """
        new_comment = Comment(task_id=task_id, author_id=author_id, text=text)
        self.session.add(instance=new_comment)
        await self.session.flush()

        return CommentRead.model_validate(new_comment)

    async def get_comments_by_task_id(self, task_id: int) -> list[CommentRead]:
        """
        Получает все комментарии к задаче, отсортированные по времени создания

        Args:
            task_id - ID задачи

        Returns:
            Список комментариев к задаче. Если нет комментариев или задачи - пустой список
        """
        stmt = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at.asc())
        )
        result = await self.session.execute(stmt)
        comments = result.scalars().all()

        return [CommentRead.model_validate(c) for c in comments]
