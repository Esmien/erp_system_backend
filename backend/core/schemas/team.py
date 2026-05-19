from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List

from backend.core.schemas.user import UserRead


class TeamBase(BaseModel):
    name: str
    description: str | None = None


class TeamRead(TeamBase):
    id: int
    created_at: datetime
    invite_code: str

    model_config = ConfigDict(from_attributes=True)


class TeamWithMembersRead(TeamRead):
    members: List[UserRead] = []


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
