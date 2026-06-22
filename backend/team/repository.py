from typing import Literal, Protocol, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, selectinload
from sqlalchemy.orm.attributes import set_committed_value

from backend.core.base_repository import BaseRepository
from backend.team.models import Team
from backend.team.schemas import TeamRead, TeamWithMembersRead
from backend.user.models import User


# Для аннотаций объектов с наличием ID
class HasId(Protocol):
    id: Mapped[int]


ModelT = TypeVar("ModelT", bound=HasId)


class TeamRepository(BaseRepository[Team, TeamWithMembersRead]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Team, dto=TeamWithMembersRead)

    async def _get_instance(self, obj_id: int) -> Team | None:
        """
        Переопределение метода базового класса.
        Все CRUD теперь подтягивают участников через selectinload

        Args:
            obj_id - ID искомого объекта

        Returns:
            ORM-модель команды со списком участников или None, если не нашлась
        """
        stmt = select(self.model).where(self.model.id == obj_id).options(selectinload(self.model.members))
        result = await self.session.execute(statement=stmt)
        return result.scalar_one_or_none()

    async def _get_obj_model_by_id(self, class_: type[ModelT], obj_id: int, for_update: bool = False) -> ModelT | None:
        """
        Получает из БД инстанс алхимии по ID и переданному классу модели

        Args:
            class_ - название класса модели, чей инстанс нужно получить из БД
            obj_id - ID для поиска
            for_update - флаг для блокировки транзакции

        Returns:
            Готовая искомая модель алхимии или None, если ничего не нашлось
        """
        return await self.session.get(class_, obj_id, with_for_update=for_update)

    async def get_team_model_by_field(self, field: Literal["name", "invite_code"], value: str) -> TeamRead | None:
        """
        Получает команду по параметру поиска

        Args:
            field - поле для поиска
            value - значение поля

        Returns:
            Готовый DTO команды или None, если не нашлась
        """
        search_field = getattr(Team, field)
        stmt = select(Team).where(search_field == value)
        result = await self.session.execute(statement=stmt)
        team = result.scalar_one_or_none()

        return TeamRead.model_validate(obj=team) if team else None

    async def create(self, **kwargs) -> TeamWithMembersRead:
        """
        Переопределяем базовый метод создания, чтобы избежать ошибки MissingGreenlet
        при валидации схемы, ожидающей вложенный список участников.
        """
        instance = self.model(**kwargs)
        self.session.add(instance=instance)
        await self.session.flush()

        # Обновляем поля из БД
        await self.session.refresh(instance=instance)

        # Команда только что создана, участников в ней 100% еще нет.
        # Явно задаем пустой список, чтобы Pydantic не триггерил ленивую загрузку
        set_committed_value(instance, "members", [])

        return self.dto.model_validate(obj=instance)

    async def add_user_to_team(self, user_id: int, team_id: int) -> bool:
        """
        Добавляет пользователя в команду

        Args:
            user - модель пользователя для добавления в команду
            team_id - ID целевой команды
        """
        # Прокидываем флаг для блокировки транзакции
        # для защиты от попыток добавить пользователя в 2 команды одновременно
        user = await self._get_obj_model_by_id(class_=User, obj_id=user_id, for_update=True)
        team = await self._get_obj_model_by_id(class_=Team, obj_id=team_id)

        if not user:
            return False

        if not team:
            return False

        user.team_id = team_id
        self.session.add(instance=user)
        await self.session.flush()

        return True
