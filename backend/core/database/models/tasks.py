from __future__ import annotations
from typing import TYPE_CHECKING

import datetime

from sqlalchemy import String, Text, Date, ForeignKey, CheckConstraint, DateTime, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.constants import TaskStatus
from backend.core.database.engine import Base


if TYPE_CHECKING:
    from backend.core.database.models.users import User

ALLOWED_STATUSES = ", ".join(f"'{status}'" for status in TaskStatus)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), comment="Название задачи")
    description: Mapped[str | None] = mapped_column(Text, comment="Подробности задачи")
    expire: Mapped[datetime.date | None] = mapped_column(Date, comment="Дедлайн")
    comments: Mapped[list["Comment"]] = relationship(back_populates="task")
    status: Mapped[str] = mapped_column(
        SQLEnum(
            TaskStatus,
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

    __table_args__ = (
        CheckConstraint(
            f"status IN ({ALLOWED_STATUSES})", name="check_valid_status_name"
        ),
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str | None] = mapped_column(Text, comment="Комментарий к задаче")
    task_id: Mapped[int] = mapped_column(
        ForeignKey(column="tasks.id", ondelete="CASCADE")
    )
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey(column="users.id", ondelete="SET NULL")
    )
    task: Mapped[Task] = relationship(back_populates="comments")
    author: Mapped[User | None] = relationship(back_populates="comments")

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
