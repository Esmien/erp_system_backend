from pydantic import BaseModel, ConfigDict

from backend.core.constants import AccessLevel


class AccessRules(BaseModel):
    """Схема прав доступа на основе действий"""

    create: AccessLevel | None = None
    read: AccessLevel | None = None
    update: AccessLevel | None = None
    delete: AccessLevel | None = None
    change_status: AccessLevel | None = None


class PermissionsBase(BaseModel):
    """Базовый класс с набором всех возможных прав"""

    policies: dict = {}


class RBACPermissions(PermissionsBase):
    """Схема с правами"""

    model_config = ConfigDict(extra="forbid")


class AccessRuleDTO(PermissionsBase):
    """Полный слепок правила доступа из БД для передачи в слой сервисов."""

    id: int
    business_element_id: int
    role_id: int

    model_config = ConfigDict(from_attributes=True)


class AccessContextDTO(BaseModel):
    """
    DTO-схема для формирования и передачи контекста в метод проверки прав.
    Используется там, где обычной ролевой проверки недостаточно
    и требуется проверить пользователя на причастность
    """

    is_author: bool = False
    is_participant: bool = False

    model_config = ConfigDict(extra="forbid")
