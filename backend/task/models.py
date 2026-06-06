# Для аннотаций во избежание циклических импортов
from __future__ import annotations
from typing import TYPE_CHECKING

import datetime

from sqlalchemy import String, Text, Date, ForeignKey, CheckConstraint, DateTime, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.constants import TaskStatus
from backend.core.database.engine import Base

# Для аннотаций во избежание циклических импортов
if TYPE_CHECKING:
    from backend.user.models import User
    from backend.comment.models import Comment

# Собираем статусы в строку для кастомных констрейтов на уровне БД.
# Без них повторные миграции падают
ALLOWED_STATUSES = ", ".join(f"'{status}'" for status in TaskStatus)


class Task(Base):
    """
    ORM-модель таблицы с задачами
    Связана с комментариями (Comment), One to Many
    Связана с авторами и исполнителями (User) по полям created_tasks для авторов и got_tasks для исполнителей
    Статусы защищены от неверных значений констрейтами на стороне БД
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), comment="Название задачи")
    description: Mapped[str | None] = mapped_column(Text, comment="Подробности задачи")
    expire: Mapped[datetime.date | None] = mapped_column(Date, comment="Дедлайн")
    comments: Mapped[list[Comment]] = relationship(back_populates="task")
    status: Mapped[str] = mapped_column(
        SQLEnum(
            TaskStatus,
            # Отключаем нативный Postgres Enum, чтобы миграции не падали
            native_enum=False,
            length=50,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=TaskStatus.OPEN,
    )

    author_id: Mapped[int | None] = mapped_column(
        ForeignKey(column="users.id", ondelete="SET NULL")
    )
    executor_id: Mapped[int | None] = mapped_column(
        ForeignKey(column="users.id", ondelete="SET NULL")
    )
    author: Mapped[User | None] = relationship(
        foreign_keys=[author_id], back_populates="created_tasks"
    )
    executor: Mapped[User | None] = relationship(
        foreign_keys=[executor_id], back_populates="got_tasks"
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Создаем кастомные констрейты в Postgres
    __table_args__ = (
        CheckConstraint(
            f"status IN ({ALLOWED_STATUSES})", name="check_valid_status_name"
        ),
    )

    def __str__(self) -> str:
        return f"Название: {self.title}, дедлайн: {self.expire}, статус: {self.status}"
