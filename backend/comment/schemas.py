from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class CommentBase(BaseModel):
    """Базовая схема комментария"""

    text: str = Field(..., min_length=1, description="Текст комментария")


class CommentCreate(CommentBase):
    """Схема для создания комментария"""

    pass


class CommentUpdate(CommentBase):
    """Схема для обновления комментариев"""

    pass


class CommentRead(CommentBase):
    """Схема для сериализации модели комментария перед отдачей клиенту"""

    id: int
    task_id: int
    author_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
