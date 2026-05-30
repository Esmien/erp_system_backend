from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base
from backend.task.models import Task
from backend.user.models import User


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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
