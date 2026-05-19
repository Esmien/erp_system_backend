from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List

from backend.core.schemas.user import UserRead


class TeamBase(BaseModel):
    name: str
    description: str | None = None


class TeamRead(TeamBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamWithMembersRead(TeamRead):
    members: List[UserRead] = []


class TeamCreate(TeamBase):
    pass
