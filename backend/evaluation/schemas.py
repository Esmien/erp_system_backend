from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class EvaluationBase(BaseModel):
    value: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class EvaluationCreate(EvaluationBase):
    """Схема для FastAPI роутера (только то, что вводит юзер)"""

    pass


class EvaluationCreateDTO(EvaluationBase):
    """Схема для передачи из Сервиса в Репозиторий (полные данные)"""

    task_id: int
    evaluator_id: int


class EvaluationRead(EvaluationBase):
    id: int
    task_id: int
    created_at: datetime
    evaluator_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class UserStatisticsRead(BaseModel):
    average_evaluation: float | None
    tasks_evaluated_count: int
