from pydantic import BaseModel, ConfigDict, Field

from backend.user.schemas import UserRead


class TeamBase(BaseModel):
    """Базовая схема команды"""

    name: str
    description: str | None = None


class TeamRead(TeamBase):
    """Схема для отправки клиенту"""

    id: int
    invite_code: str

    model_config = ConfigDict(from_attributes=True)


class TeamWithMembersRead(TeamRead):
    """Схема для отправки клиенту ВМЕСТЕ с участниками команды"""

    members: list[UserRead] = Field(default_factory=list)


class TeamCreate(TeamBase):
    """Схема для создания команды"""

    pass


class TeamJoin(BaseModel):
    """Схема инвайт кода для использования при вступлении в команду"""

    invite_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        examples=["A7F2X9"],
        description="Уникальный 6-значный код приглашения",
    )
