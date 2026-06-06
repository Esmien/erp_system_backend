from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.comment.models import Comment
from backend.comment.schemas import CommentRead
from backend.core.base_repository import BaseRepository


class CommentRepository(BaseRepository[Comment, CommentRead]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Comment, dto=CommentRead)

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
