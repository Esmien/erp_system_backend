# Для аннотаций во избежание циклических импортов
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database.engine import Base

# Для аннотаций во избежание циклических импортов
if TYPE_CHECKING:
    from backend.user.models import User


class Team(Base):
    """
    ORM-модель таблицы с командами
    Связана с участниками (список User), связь One to Many, members <-> team
    """

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="Название команды")
    description: Mapped[str | None] = mapped_column(Text, comment="Описание команды")
    invite_code: Mapped[str] = mapped_column(
        String(6),
        unique=True,
        nullable=False,
        comment="Код приглашения в команду, генерируется автоматически",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания команды",
    )
    members: Mapped[list[User]] = relationship(back_populates="team", lazy="selectin")

    def __str__(self) -> str:
        return f"Название: {self.name},  код приглашения: {self.invite_code}"
