from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.database.models import User
from backend.core.database.models.teams import Team
from backend.core.schemas.team import TeamCreate


class TeamRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_team_by_id(self, team_id: int) -> Team | None:
        stmt = (
            select(Team).where(Team.id == team_id).options(selectinload(Team.members))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def check_name_exists(self, name: str) -> bool:
        stmt = select(Team).where(Team.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def check_invite_code_exists(self, code: str) -> bool:
        stmt = select(Team).where(Team.invite_code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_team_by_invite_code(self, code: str) -> Team | None:
        stmt = select(Team).where(Team.invite_code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_team(self, team_in: TeamCreate, invite_code: str) -> Team:
        new_team = Team(
            name=team_in.name, description=team_in.description, invite_code=invite_code
        )
        self.session.add(new_team)
        await self.session.commit()
        await self.session.refresh(new_team)
        return new_team

    async def add_user_to_team(self, user: User, team_id: int) -> None:
        user.team_id = team_id
        self.session.add(user)
        await self.session.commit()
