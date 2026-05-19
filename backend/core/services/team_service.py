import secrets
import string

from backend.core.database.models import User
from backend.core.database.repository.team import TeamRepository
from backend.core.schemas.team import TeamCreate
from backend.exceptions import (
    TeamDoesNotExistsError,
    TeamAlreadyExistsError,
    UserAlreadyInTeamError,
)


class TeamService:
    def __init__(self, repo: TeamRepository):
        self.repo = repo

    @staticmethod
    def generate_invite_code(length: int = 6) -> str:
        """Генерирует криптографически надежный код из заглавных букв и цифр"""
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def get_team(self, team_id: int):
        team = await self.repo.get_team_by_id(team_id)

        if team is None:
            raise TeamDoesNotExistsError

        return team

    async def create_team(self, team_in: TeamCreate):
        is_exists = await self.repo.check_name_exists(team_in.name)

        if is_exists:
            raise TeamAlreadyExistsError

        while True:
            code = self.generate_invite_code()
            is_code_exists = await self.repo.check_invite_code_exists(code)

            if not is_code_exists:
                break

        return await self.repo.create_team(team_in=team_in, invite_code=code)

    async def join_team(self, user: User, invite_code: str):
        if user.team_id is not None:
            raise UserAlreadyInTeamError

        team = await self.repo.get_team_by_invite_code(invite_code)

        if not team:
            raise TeamDoesNotExistsError

        await self.repo.add_user_to_team(user, team.id)
        return team
