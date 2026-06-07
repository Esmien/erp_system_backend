from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, ForeignKey

from backend.core.database.engine import Base


class BusinessElement(Base):
    """ORM-модель таблицы для хранения бизнес-сущностей"""

    __tablename__ = "business_elements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, comment="Название бизнес-сущности"
    )


class AccessRule(Base):
    """
    ORM-модель правил доступа: определяет, какие права есть у роли на ресурс
    Связана c ролью пользователя (Role) и элементами бизнес-логики (BusinessElement)
    Матрица прав реализована при помощи политик в формате JSONB
    """

    __tablename__ = "access_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    business_element_id: Mapped[int] = mapped_column(
        ForeignKey("business_elements.id"),
        nullable=False,
        index=True,
        comment="ID бизнес-сущности для назначения прав",
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"),
        nullable=False,
        index=True,
        comment="ID роли, для которой назначаются права доступа",
    )
    business_element: Mapped[BusinessElement] = relationship(backref="access_rules")
    role = relationship("Role")

    policies: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        comment="Матрица прав доступа к элементам для ролей с учетом контекста",
    )
