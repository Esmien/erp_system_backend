from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.core.enums import TaskStatus
from backend.exceptions import DatetimeCompatibleError


class TaskBase(BaseModel):
    """Базовая схема задачи"""

    title: str = Field(..., max_length=50, description="Название задачи")
    description: str | None = Field(default=None, description="Подробности задачи")
    expire: date | None = Field(default=None, description="Дедлайн")
    status: TaskStatus = Field(default=TaskStatus.OPEN, description="Статус задачи")


class TaskCreate(TaskBase):
    """Схема задачи для создания с валидацией даты дедлайна"""

    @field_validator("expire", mode="after")
    @classmethod
    def check_date(cls, value: date) -> date:
        if value < date.today():
            raise DatetimeCompatibleError(
                "Нельзя создать задачу с датой окончания раньше текущей"
            )
        return value


class TaskRead(TaskBase):
    """Схема задачи для возвращения клиенту"""

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
    """Схема для смены статуса"""

    status: TaskStatus = Field(..., description="Новый статус задачи")

    model_config = ConfigDict(extra="forbid")
