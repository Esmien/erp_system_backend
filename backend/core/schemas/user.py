from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict


class RoleBase(BaseModel):
    name: str


class RoleRead(RoleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    name: str = Field(..., examples=["Иван"])
    surname: str | None = Field(default=None, examples=["Иванович"])
    last_name: str | None = Field(default=None, examples=["Иванов"])
    team_id: int | None = Field(default=None)


class UserRead(UserBase):
    id: int
    is_active: bool
    role: RoleRead
    model_config = ConfigDict(from_attributes=True)


class UserRegister(UserBase):
    password: str = Field(
        ..., min_length=3, max_length=72, examples=["secret_password"]
    )
    repeat_password: str = Field(
        ..., min_length=3, max_length=72, examples=["secret_password"]
    )
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.repeat_password:
            raise ValueError("Пароли не совпадают!")
        return self


class UserChangeStatus(BaseModel):
    message: str
    user: UserRead


class Token(BaseModel):
    access_token: str
    token_type: str
