from pydantic import BaseModel, ConfigDict

from backend.core.constants import AccessLevel


class AccessRules(BaseModel):
    create: AccessLevel | None = None
    read: AccessLevel | None = None
    update: AccessLevel | None = None
    delete: AccessLevel | None = None
    change_status: AccessLevel | None = None


class PermissionsBase(BaseModel):
    """Базовый класс с набором всех возможных прав"""

    policies: dict = {}


class RBACPermissions(PermissionsBase):
    model_config = ConfigDict(extra="forbid")


class AccessRuleDTO(PermissionsBase):
    """
    Полный слепок правила доступа из БД для передачи в слой сервисов.
    """

    id: int
    business_element_id: int
    role_id: int

    model_config = ConfigDict(from_attributes=True)


class AccessContextDTO(BaseModel):
    is_author: bool = False
    is_participant: bool = False

    model_config = ConfigDict(extra="forbid")
