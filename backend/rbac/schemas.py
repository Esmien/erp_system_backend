from pydantic import BaseModel, ConfigDict


class PermissionsBase(BaseModel):
    """Базовый класс с набором всех возможных прав"""

    read_permission: bool = False
    read_all_permission: bool = False
    create_permission: bool = False
    update_permission: bool = False
    update_all_permission: bool = False
    delete_permission: bool = False
    delete_all_permission: bool = False


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
