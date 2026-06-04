from datetime import datetime

from sqlalchemy import ForeignKey, CheckConstraint, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database.engine import Base


class Evaluation(Base):
    """
    ORM-модель оценок задач.
    Связана с задачей (Task) и оценивающим сотрудником(User).
    Связь Evaluation <-> Task – One to One
    Связь User <-> Evaluation – On to Many
    """

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Ограничение на диапазон оценок от 1 до 5
    value: Mapped[int] = mapped_column(
        CheckConstraint(
            "value >= 1 AND value <= 5", name="check_valid_evaluation_value"
        )
    )
    # Комментарий (пояснения) к оценке
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), unique=True
    )
    evaluator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
