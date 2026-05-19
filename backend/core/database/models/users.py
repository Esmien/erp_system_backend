from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, ForeignKey, Boolean, CheckConstraint
from sqlalchemy import Enum as SQLEnum

from backend.core.constants import RoleName
from backend.core.database.engine import Base


if TYPE_CHECKING:
    from backend.core.database.models.teams import Team
    from backend.core.database.models.tasks import Task, Comment


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
    team: Mapped[Team | None] = relationship(back_populates="members")
    created_tasks: Mapped[list[Task]] = relationship(
        foreign_keys="[Task.author_id]", back_populates="author"
    )
    got_tasks: Mapped[list[Task]] = relationship(
        foreign_keys="[Task.executor_id]", back_populates="executor"
    )
    comments: Mapped[list[Comment]] = relationship(back_populates="author")


ALLOWED_ROLES = ", ".join(f"'{role}'" for role in RoleName)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(
        SQLEnum(
            RoleName,
            native_enum=False,
            length=50,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        unique=True,
    )
    users: Mapped[list["User"]] = relationship(back_populates="role", lazy="selectin")

    __table_args__ = (
        CheckConstraint(f"name IN ({ALLOWED_ROLES})", name="check_valid_role_name"),
    )
