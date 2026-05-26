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


class UserRead(UserBase):
    id: int
    is_active: bool
    role: RoleRead
    team_id: int | None = Field(default=None)
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


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, examples=["Алексей"])
    surname: str | None = Field(default=None, examples=["Алексеевич"])
    last_name: str | None = Field(default=None, examples=["Алексеев"])

    model_config = ConfigDict(extra="forbid")


class Token(BaseModel):
    access_token: str
    token_type: str


class RoleDTO(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserBaseDTO(UserBase):
    hashed_password: str
    is_active: bool
    role_id: int


class UserCreateDTO(UserBaseDTO):
    pass


class UserDTO(UserBaseDTO):
    id: int
    role: RoleDTO | None = None
    team_id: int | None = None

    model_config = ConfigDict(from_attributes=True)
