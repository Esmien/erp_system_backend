from backend.core.database.repository.team import TeamRepository
from backend.core.schemas.team import TeamCreate
from backend.exceptions import TeamDoesNotExistsError, TeamAlreadyExistsError


class TeamService:
    def __init__(self, repo: TeamRepository):
        self.repo = repo

    async def get_team(self, team_id: int):
        team = await self.repo.get_team_by_id(team_id)

        if team is None:
            raise TeamDoesNotExistsError

        return team

    async def create_team(self, team_in: TeamCreate):
        is_exists = await self.repo.check_name_exists(team_in.name)

        if is_exists:
            raise TeamAlreadyExistsError

        return await self.repo.create_team(team_in)
