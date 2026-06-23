from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from backend.exceptions import PasswordsMismatchError


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


class UserLogin(BaseModel):
    """Схема для аутентификации пользователя"""

    username: EmailStr
    password: str


class UserRegister(UserBase):
    """Схема с полями для регистрации и валидацией пароля"""

    password: str = Field(..., min_length=3, max_length=72, examples=["secret_password"])
    repeat_password: str = Field(..., min_length=3, max_length=72, examples=["secret_password"])
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.repeat_password:
            raise PasswordsMismatchError("Пароли не совпадают!")
        return self


class UserChangeStatus(BaseModel):
    """Схема для смены статуса пользователя (is_active)"""

    message: str
    user: UserRead


class UserUpdate(BaseModel):
    """Схема для обновления данных пользователя"""

    name: str | None = Field(default=None, examples=["Алексей"])
    surname: str | None = Field(default=None, examples=["Алексеевич"])
    last_name: str | None = Field(default=None, examples=["Алексеев"])

    model_config = ConfigDict(extra="forbid")


class Token(BaseModel):
    """Схема модели JWT-токена"""

    access_token: str
    token_type: str


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

    model_config = ConfigDict(from_attributes=True)
