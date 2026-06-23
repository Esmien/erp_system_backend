import secrets
import string

from loguru import logger

from backend.core.base_service import BaseService
from backend.core.config import settings
from backend.core.enums import Action, BusinessElementName
from backend.exceptions import (
    TeamAlreadyExistError,
    TeamDoesNotExistError,
    UserAlreadyInTeamError,
)
from backend.rbac.schemas import AccessContextDTO
from backend.team.repository import TeamRepository
from backend.team.schemas import TeamCreate, TeamRead, TeamWithMembersRead
from backend.user.schemas import UserDTO


class TeamService(BaseService[TeamWithMembersRead]):
    @property
    def repository(self) -> TeamRepository:
        return self.uow.teams

    @property
    def business_element(self) -> BusinessElementName:
        return BusinessElementName.TEAMS

    @property
    def not_found_exception(self) -> Exception:
        return TeamDoesNotExistError("Команда не найдена")

    def build_abac_context(self, obj: TeamRead, user: UserDTO) -> AccessContextDTO:
        return AccessContextDTO(is_author=False, is_participant=obj.id == user.team_id)

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

    async def get_team(self, team_id: int, user: UserDTO) -> TeamWithMembersRead:
        """
        Получает полную модель команды по ее ID

        Args:
            team_id - ID искомой команды
            user - пользователь, который запрашивает данные команды

        Returns:
            Модель команды с участниками

        Raises:
            AccessDeniedError - если пользователь не в этой команде
            TeamDoesNotExistsError - если команды с таким названием не существует
        """
        team = await self.get_or_raise(obj_id=team_id)
        # Проверка прав - можно только участникам или руководителям
        await self.check_permissions(
            user=user,
            action=Action.READ,
            obj=team,
            error_msg="Вы не можете посмотреть данные этой команды",
        )

        logger.info(f"Успешно получены данные команды ID: {team.id}, Название: {team.name}.")
        return team

    async def create_team(self, team_in: TeamCreate, user: UserDTO) -> TeamRead:
        """
        Создает команду

        Args:
            team_in - Pydantic-схема со всеми необходимыми для создания команды полями

        Returns:
            Модель созданной команды

        Raises:
            AccessDeniedError - если нет прав на создание команды
            TeamAlreadyExistsError - если команда с таким названием уже существует
        """
        # Проверка прав - можно только руководителям
        await self.check_permissions(
            user=user,
            action=Action.CREATE,
            error_msg="Недостаточно прав для создания команды",
        )

        # Проверяем существование команды, чтобы избежать дубликатов
        team_by_name = await self.repository.get_team_model_by_field(field="name", value=team_in.name)

        if team_by_name:
            logger.info(f"Команда с названием {team_in.name} уже существует.")
            raise TeamAlreadyExistError("Команда с таким названием уже существует")

        # Запускаем генерацию инвайт-кода в цикле, чтобы он был уникальным.
        # Если совпадений в Бд не найдено, то цикл завершается
        while True:
            code = self.generate_invite_code()
            team_by_code = await self.repository.get_team_model_by_field(field="invite_code", value=code)

            if not team_by_code:
                logger.info(f"Инвайт код для команды {team_in.name} успешно сгенерирован.")
                break

        created_team = await self.repository.create(**team_in.model_dump(), invite_code=code)

        await self.uow.commit()

        logger.info(f"Команда {created_team.name} успешно создана.")
        return created_team

    async def join_team(self, user: UserDTO, invite_code: str) -> TeamRead:
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
        # Проверка на присутствие в какой-нибудь команде
        if user.team_id is not None:
            logger.info(f"Пользователь ID: {user.id}, Email: {user.email} уже состоит в команде ID: {user.team_id}.")
            raise UserAlreadyInTeamError("Вы уже состоите в команде")

        # Ищем команду по инвайт коду и вступаем, если все ок
        team = await self.repository.get_team_model_by_field(field="invite_code", value=invite_code)

        if not team:
            logger.info(f"Инвайт код {invite_code} не найден.")
            raise TeamDoesNotExistError("Команда с таким кодом не найдена")

        await self.repository.add_user_to_team(user_id=user.id, team_id=team.id)
        await self.uow.commit()

        logger.info(f"Пользователь ID: {user.id} добавлен в команду ID: {team.id}")
        return team
