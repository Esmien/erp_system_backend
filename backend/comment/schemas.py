from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class CommentBase(BaseModel):
    text: str = Field(..., min_length=1, description="Текст комментария")


class CommentCreate(CommentBase):
    pass


class CommentUpdate(CommentBase):
    pass


class CommentRead(CommentBase):
    id: int
    task_id: int
    author_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
