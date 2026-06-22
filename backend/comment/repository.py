from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.comment.models import Comment
from backend.comment.schemas import CommentRead
from backend.core.base_repository import BaseRepository


class CommentRepository(BaseRepository[Comment, CommentRead]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Comment, dto=CommentRead)

    async def get_comments_by_task_id(self, task_id: int, offset: int, limit: int) -> tuple[list[CommentRead], int]:
        """
        Получает все комментарии к задаче, отсортированные по времени создания

        Args:
            task_id - ID задачи
            offset - смещение указателя при чтении большого количества данных
            limit - ограничение на количество выдаваемых за раз данных

        Returns:
            Пагинированный список комментариев к задаче и общее количество комментов
        """
        stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at.asc())

        return await self._paginate_statement(stmt=stmt, offset=offset, limit=limit)
