from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import String, DateTime, func, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database.engine import Base


if TYPE_CHECKING:
    from backend.user.models import User


meeting_participants = Table(
    "meeting_participants",
    Base.metadata,
    Column(
        "meeting_id", ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    theme: Mapped[str] = mapped_column(String(100), comment="Тема встречи")
    datetime_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), comment="Начало в", nullable=False
    )
    datetime_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Окончание в ", nullable=True
    )

    author_id: Mapped[int | None] = mapped_column(
        ForeignKey(column="users.id", ondelete="SET NULL")
    )
    author: Mapped[User | None] = relationship(
        foreign_keys=[author_id], back_populates="created_meetings"
    )

    participants: Mapped[list[User]] = relationship(
        secondary=meeting_participants, back_populates="participant_meetings"
    )
