from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleBase(BaseModel):
    name: str


class RoleRead(RoleBase):
    """Схема для возврата модели роли клиенту"""

    id: int
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    """Схема с базовыми параметрами пользователя"""

    email: EmailStr = Field(..., examples=["user@example.com"])
    name: str = Field(..., examples=["Иван"])
    surname: str | None = Field(default=None, examples=["Иванович"])
    last_name: str | None = Field(default=None, examples=["Иванов"])


class UserRead(UserBase):
    """Схема для возврата клиенту"""

    id: int
    is_active: bool
    role: RoleRead
    team_id: int | None = Field(default=None)
    model_config = ConfigDict(from_attributes=True)


class UserChangeStatus(BaseModel):
    """Схема для смены статуса пользователя (is_active)"""

    message: str
    user: UserRead


class UserUpdate(BaseModel):
    """Схема для обновления данных пользователя"""

    name: str | None = Field(default=None, examples=["Алексей"])
    surname: str | None = Field(default=None, examples=["Алексеевич"])
    last_name: str | None = Field(default=None, examples=["Алексеев"])
    tg_id: int | None = Field(default=None, examples=["123456789"])

    model_config = ConfigDict(extra="forbid")


class RoleForCodeDTO(RoleBase):
    pass


class RoleDTO(RoleBase):
    """DTO-схема роли для передачи между слоями"""

    id: int

    model_config = ConfigDict(from_attributes=True)


class UserBaseDTO(UserBase):
    """Базовая DTO-схема пользователя"""

    hashed_password: str
    is_active: bool
    role_id: int


class UserCreateDTO(UserBaseDTO):
    """DTO-схема создания пользователя для передачи между слоями"""

    pass


class UserDTO(UserBaseDTO):
    """Полная DTO-схема для передачи пользователя между слоями"""

    id: int
    role: RoleDTO | None = None
    team_id: int | None = None
    tg_id: int | None = None

    model_config = ConfigDict(from_attributes=True)
