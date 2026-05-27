from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field
from backend.core.constants import TaskStatus


class TaskBase(BaseModel):
    title: str = Field(..., max_length=50, description="Название задачи")
    description: str | None = Field(default=None, description="Подробности задачи")
    expire: date | None = Field(default=None, description="Дедлайн")
    status: TaskStatus = Field(default=TaskStatus.OPEN, description="Статус задачи")


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: int
    author_id: int | None
    created_at: datetime
    executor_id: int | None = Field(default=None, description="ID исполнителя")

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    """Схема для редактирования текста/дедлайна/исполнителя задачи"""

    title: str | None = Field(default=None, max_length=50)
    description: str | None = None
    expire: date | None = None
    executor_id: int | None = None

    model_config = ConfigDict(extra="forbid")


class TaskChangeStatus(BaseModel):
    """Схема ИСКЛЮЧИТЕЛЬНО для смены статуса"""

    status: TaskStatus = Field(..., description="Новый статус задачи")

    model_config = ConfigDict(extra="forbid")


class CommentBase(BaseModel):
    text: str = Field(..., min_length=1, description="Текст комментария")


class CommentCreate(CommentBase):
    pass


class CommentRead(CommentBase):
    id: int
    task_id: int
    author_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
