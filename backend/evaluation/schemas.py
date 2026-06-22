from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EvaluationBase(BaseModel):
    """Базовая схема оценки"""

    value: int = Field(ge=1, le=5)
    # Комментарий к оценке
    comment: str | None = Field(default=None, max_length=1000)


class EvaluationCreate(EvaluationBase):
    """Схема для FastAPI роутера (только то, что вводит юзер)"""

    pass


class EvaluationCreateDTO(EvaluationBase):
    """Схема для передачи из Сервиса в Репозиторий (полные данные)"""

    task_id: int
    evaluator_id: int


class EvaluationRead(EvaluationBase):
    """Схема оценки для сериализации клиенту"""

    id: int
    task_id: int
    created_at: datetime
    evaluator_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class UserStatisticsRead(BaseModel):
    """Схема для сбора статистики по оценкам для отдельных пользователей"""

    average_evaluation: float | None
    tasks_evaluated_count: int
