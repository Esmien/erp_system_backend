from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import String, DateTime, func, ForeignKey, Table, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.constants import MeetingStatus
from backend.core.database.engine import Base


# Для защиты от циклических импортов
if TYPE_CHECKING:
    from backend.user.models import User


# Связующая таблица для связи встреч и пользователей (Many to Many)
meeting_participants = Table(
    "meeting_participants",
    Base.metadata,
    Column(
        "meeting_id", ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Meeting(Base):
    """
    ORM-модель встреч.
    Связана с участниками (list[User], MtM) и автором (User, MtO)
    Связть Many to Many реализована через таблицу meeting_participants
    """

    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    theme: Mapped[str] = mapped_column(String(100), comment="Тема встречи")
    datetime_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), comment="Начало в", nullable=False
    )
    datetime_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Окончание в ", nullable=True
    )
    status: Mapped[str] = mapped_column(
        # Превращаем питоновский Enum в строчку для БД,
        # чтобы не было конфликтов типов при повторных миграциях
        SQLEnum(
            MeetingStatus,
            native_enum=False,
            length=50,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=MeetingStatus.PENDING,
        index=True,
        comment="Статус встречи",
    )

    # Связь с автором
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey(column="users.id", ondelete="SET NULL"),
        comment="ID автора встречи",
        index=True,
    )
    author: Mapped[User | None] = relationship(
        foreign_keys=[author_id], back_populates="created_meetings"
    )

    # Связь с участниками
    participants: Mapped[list[User]] = relationship(
        secondary=meeting_participants, back_populates="participant_meetings"
    )
