import secrets
import string

from backend.core.config import settings
from backend.team.repository import TeamRepository
from backend.team.schemas import TeamCreate, TeamWithMembersRead, TeamRead
from backend.exceptions import (
    TeamDoesNotExistsError,
    TeamAlreadyExistsError,
    UserAlreadyInTeamError,
)
from backend.user.schemas import UserRead


class TeamService:
    def __init__(self, repo: TeamRepository):
        self.repo = repo

    @staticmethod
    def generate_invite_code(length: int = settings.inv_code.CODE_LENGTH) -> str:
        """
        Генерирует криптографически надежный инвайт-код из заглавных букв и цифр.

        Args:
            length - длина кода (по умолчанию берётся из settings.inv_code)

        Returns:
            Строка из заглавных букв и цифр заданной длины
        """
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def get_team(self, team_id: int) -> TeamWithMembersRead:
        """
        Получает полную модель команды по ее ID

        Args:
            team_id - ID искомой команды

        Returns:
            Модель команды

        Raises:
            TeamDoesNotExistsError - если команды с таким названием не существует
        """
        team = await self.repo.get_team_by_id(team_id=team_id)

        if team is None:
            raise TeamDoesNotExistsError

        return team

    async def create_team(self, team_in: TeamCreate) -> TeamRead:
        """
        Создает команду

        Args:
            team_in - Pydantic-схема со всеми необходимыми для создания команды полями

        Returns:
            Модель созданной команды

        Raises:
            TeamAlreadyExistsError - если команда с таким названием уже существует
        """
        # Проверяем существование команды, чтобы избежать дубликатов
        is_exists = await self.repo.check_team_name_exists(team_name=team_in.name)

        if is_exists:
            raise TeamAlreadyExistsError

        # Запускаем генерацию инвайт-кода в цикле, чтобы он был уникальным.
        # Если совпадений в Бд не найдено, то цикл завершается
        while True:
            code = self.generate_invite_code()
            is_code_exists = await self.repo.check_invite_code_exists(code=code)

            if not is_code_exists:
                break

        return await self.repo.create_team(team_in=team_in, invite_code=code)

    async def join_team(self, user: UserRead, invite_code: str) -> TeamRead:
        """
        Регистрирует пользователя в команде

        Args:
            user - пользователь, который хочет добавиться в команду
            invite_code - уникальный код для вступления в команду

        Returns:
            Модель команды, в которую вступил пользователь

        Raises:
            UserAlreadyInTeamError - если пользователь уже в какой-либо команде
            TeamDoesNotExistsError - если инвайт код не подошел ни к одной команде
        """
        if user.team_id is not None:
            raise UserAlreadyInTeamError

        team = await self.repo.get_team_by_invite_code(code=invite_code)

        if not team:
            raise TeamDoesNotExistsError

        await self.repo.add_user_to_team(user_id=user.id, team_id=team.id)
        return team
