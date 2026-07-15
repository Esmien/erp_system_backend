from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from backend.exceptions import PasswordsMismatchError
from backend.user.schemas import UserBase


class UserLogin(BaseModel):
    """Схема для аутентификации пользователя"""

    username: EmailStr
    password: str


class RegisterCode(BaseModel):
    register_code: str = Field(
        ..., min_length=6, max_length=6, description="Одноразовый код для регистрации на платформе"
    )


class UserRegister(UserBase):
    """Схема с полями для регистрации и валидацией пароля"""

    password: str = Field(..., min_length=3, max_length=72, examples=["secret_password"])
    repeat_password: str = Field(..., min_length=3, max_length=72, examples=["secret_password"])
    register_code: str = Field(
        ..., min_length=6, max_length=6, description="Одноразовый код для регистрации на платформе"
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.repeat_password:
            raise PasswordsMismatchError("Пароли не совпадают!")
        return self


class Token(BaseModel):
    """Схема модели JWT-токена"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str
