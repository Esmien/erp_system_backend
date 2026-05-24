from pydantic import BaseModel, ConfigDict, Field
from typing import List

from backend.user.schemas import UserRead


class TeamBase(BaseModel):
    name: str
    description: str | None = None


class TeamRead(TeamBase):
    id: int
    invite_code: str

    model_config = ConfigDict(from_attributes=True)


class TeamWithMembersRead(TeamRead):
    members: List[UserRead] = Field(default_factory=list)


class TeamCreate(TeamBase):
    pass


class TeamJoin(BaseModel):
    invite_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        examples=["A7F2X9"],
        description="Уникальный 6-значный код приглашения",
    )
