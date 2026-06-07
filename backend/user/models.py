# Для аннотаций во избежание циклических импортов
from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, ForeignKey, Boolean, CheckConstraint
from sqlalchemy import Enum as SQLEnum

from backend.core.constants import RoleName
from backend.core.database.engine import Base


# Для аннотаций во избежание циклических импортов
if TYPE_CHECKING:
    from backend.team.models import Team
    from backend.task.models import Task
    from backend.comment.models import Comment
    from backend.meeting.models import Meeting


class User(Base):
    """
    Основная модель пользователя.

    Имеет связи:
        Роль(Role) - Many to One, роли создаются отдельно
        Команда(Team) - Many to One, может состоять только в одной команде

        Задачи(Task) - One to Many, у пользователя может быть несколько задач.
        В задачах может быть автором (created_task <-> Task.author) и/или исполнителем (got_task <-> Task.executor)

        Комментарии(Comment) - One to Many, пользователь может оставить несколько комментариев

        Встречи(Meeting) - Many to Many, на встречах может быть несколько участников, у участников - несколько встреч.
        На встречах может быть создателем (created_meetings <-> Meeting.author)
        или участником (participant_meetings <-> Meeting.participants)
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Блок основных столбцов
    email: Mapped[str] = mapped_column(
        String, unique=True, comment="Электронная почта/логин пользователя"
    )
    hashed_password: Mapped[str] = mapped_column(
        String, comment="Зашифрованный хэшем пароль"
    )
    name: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Имя пользователя"
    )
    surname: Mapped[str | None] = mapped_column(
        String(30), nullable=True, comment="Отчество пользователя"
    )
    last_name: Mapped[str | None] = mapped_column(
        String(35), nullable=True, comment="Фамилия пользователя"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True, comment="Статус активности (True/False)"
    )

    # Блок связей
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"), index=True, comment="ID роли пользователя"
    )
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"),
        index=True,
        comment="ID команды, в которой состоит пользователь",
    )
    role: Mapped["Role"] = relationship(back_populates="users", lazy="selectin")
    team: Mapped[Team | None] = relationship(back_populates="members")

    created_tasks: Mapped[list[Task]] = relationship(
        foreign_keys="[Task.author_id]", back_populates="author"
    )
    got_tasks: Mapped[list[Task]] = relationship(
        foreign_keys="[Task.executor_id]", back_populates="executor"
    )
    comments: Mapped[list[Comment]] = relationship(back_populates="author")
    created_meetings: Mapped[list[Meeting]] = relationship(back_populates="author")
    participant_meetings: Mapped[list[Meeting]] = relationship(
        secondary="meeting_participants", back_populates="participants"
    )

    def __str__(self) -> str:
        # sqladmin будет дергать этот метод для отображения
        if self.last_name:
            return f"{self.name} {self.last_name} ({self.email})"
        return f"{self.name} ({self.email})"


# Собираем роли в строку для кастомных констрейтов на уровне БД.
# Без них повторные миграции падают
ALLOWED_ROLES = ", ".join(f"'{role}'" for role in RoleName)


class Role(Base):
    """
    ORM-модель таблицы ролей
    Связана с пользователями(список User), One to Many
    """

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
        comment="Название роли",
    )
    users: Mapped[list["User"]] = relationship(back_populates="role", lazy="selectin")

    # Создаем кастомные констрейты в Postgres
    __table_args__ = (
        CheckConstraint(f"name IN ({ALLOWED_ROLES})", name="check_valid_role_name"),
    )

    def __str__(self) -> str:
        return f"ID роли: {self.id}, название: {self.name}"
