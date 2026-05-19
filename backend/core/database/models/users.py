from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, ForeignKey, Boolean
from sqlalchemy import Enum as SQLEnum

from backend.core.database.engine import Base
from backend.core.config import RoleName


if TYPE_CHECKING:
    from backend.core.database.models.teams import Team


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    surname: Mapped[str | None] = mapped_column(String(30), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(35), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    role: Mapped["Role"] = relationship(back_populates="users", lazy="selectin")
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL")
    )
    team: Mapped[Team| None] = relationship(back_populates="members")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[RoleName] = mapped_column(
        SQLEnum(RoleName, native_enum=False, length=50), unique=True
    )
    users: Mapped[list["User"]] = relationship(back_populates="role", lazy="selectin")
