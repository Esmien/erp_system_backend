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


class TaskUpdate(TaskBase):
    title: str | None = Field(
        default=None, max_length=50, description="Название задачи"
    )
    executor_id: int | None = Field(default=None, description="ID исполнителя")

    model_config = ConfigDict(extra="forbid")


class TaskRead(TaskBase):
    id: int
    author_id: int | None
    created_at: datetime
    executor_id: int | None = Field(default=None, description="ID исполнителя")

    model_config = ConfigDict(from_attributes=True)
