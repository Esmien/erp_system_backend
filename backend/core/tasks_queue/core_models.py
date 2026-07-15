from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database.engine import Base

if TYPE_CHECKING:
    from backend.user.models import User

class AuditLog(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey(column="users.id", ondelete="SET NULL"),
        comment="ID пользователя"
    )
    action: Mapped[str] = mapped_column(String(length=50), comment="Действие над сущностью")
    entity_name: Mapped[str] = mapped_column(String(length=50), comment="Название сущности")
    entity_id: Mapped[int] = mapped_column(Integer, comment="ID сущности")

    user: Mapped[User | None] = relationship(back_populates="logs")