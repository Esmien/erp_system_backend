from typing import TypeVar, Protocol

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, Mapped

from backend.team.models import Team
from backend.team.schemas import TeamCreate, TeamRead, TeamWithMembersRead
from backend.user.models import User


class HasId(Protocol):
    id: Mapped[int]


ModelT = TypeVar("ModelT", bound=HasId)


class TeamRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_obj_model_by_id(
        self, obj: type[ModelT], obj_id: int
    ) -> ModelT | None:
        stmt = select(obj).where(obj.id == obj_id)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def _get_team_model_by_name(self, team_name: str) -> Team | None:
        stmt = select(Team).where(Team.name == team_name)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def _get_team_model_by_invite_code(self, invite_code: str) -> Team | None:
        stmt = select(Team).where(Team.invite_code == invite_code)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_team_by_id(self, team_id: int) -> TeamWithMembersRead | None:
        """
        Получает модель команды по ее ID

        Args:
            team_id - ID команды

        Returns:
            Модель команды с загруженными участниками или None, если не найдена
        """
        stmt = (
            select(Team).where(Team.id == team_id).options(selectinload(Team.members))
        )
        result = await self.session.execute(statement=stmt)

        team = result.scalar_one_or_none()

        return TeamWithMembersRead.model_validate(team) if team else None

    async def check_team_name_exists(self, team_name: str) -> bool:
        """
        Проверяет, существует ли команда по ее названию

        Args:
            team_name - название команды

        Returns:
            True - если существует, False - если нет
        """
        return await self._get_team_model_by_name(team_name=team_name) is not None

    async def check_invite_code_exists(self, code: str) -> bool:
        """
        Проверяет, существует ли переданный инвайт-код у какой-либо команды.
        Необходимо для защиты от одинаковых кодов у разных команд

        Args:
            code - код для проверки

        Returns:
            True - если существует, False - если нет
        """
        return await self._get_team_model_by_invite_code(invite_code=code) is not None

    async def get_team_by_invite_code(self, code: str) -> TeamRead | None:
        """
        Находит команду по инвайт коду

        Args:
            code - инвайт код

        Returns:
            Модель соответствующей команды или None, если код неправильный
        """
        team = await self._get_team_model_by_invite_code(invite_code=code)

        return TeamRead.model_validate(team) if team else None

    async def create_team(self, team_in: TeamCreate, invite_code: str) -> TeamRead:
        """
        Создает команду

        Args:
            team_in - Pydantic-модель команды для создания
            invite_code - сгенерированный инвайт-код для присвоения его команде

        Returns:
            Модель команды со всеми необходимыми полями
        """
        new_team = Team(
            name=team_in.name, description=team_in.description, invite_code=invite_code
        )

        self.session.add(instance=new_team)
        await self.session.commit()
        await self.session.refresh(instance=new_team)

        return TeamRead.model_validate(new_team)

    async def add_user_to_team(self, user_id: int, team_id: int) -> bool:
        """
        Добавляет пользователя в команду

        Args:
            user - модель пользователя для добавления в команду
            team_id - ID целевой команды
        """
        user = await self._get_obj_model_by_id(obj=User, obj_id=user_id)
        team = await self._get_obj_model_by_id(obj=Team, obj_id=team_id)

        if not user:
            logger.warning(f"Пользователь с ID: {user_id} не найден.")
            return False

        if not team:
            logger.warning(f"Команда с ID: {team_id} не найдена.")
            return False

        user.team_id = team_id
        self.session.add(instance=user)
        await self.session.commit()

        logger.success(f"Пользователь {user.name} добавлен в команду {team.name}.")

        return True
