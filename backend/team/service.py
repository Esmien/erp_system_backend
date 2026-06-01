import secrets
import string

from loguru import logger

from backend.core.config import settings
from backend.core.constants import BusinessElementName, Action
from backend.core.uow import IUnitOfWork
from backend.rbac.schemas import AccessContextDTO
from backend.rbac.service import RbacService
from backend.team.schemas import TeamCreate, TeamWithMembersRead, TeamRead
from backend.exceptions import (
    TeamDoesNotExistsError,
    TeamAlreadyExistsError,
    UserAlreadyInTeamError,
)
from backend.user.schemas import UserDTO


class TeamService:
    def __init__(self, uow: IUnitOfWork, rbac_service: RbacService):
        self.uow = uow
        self.rbac = rbac_service

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
        async with self.uow:
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.TEAMS,
                action=Action.READ,
                context=AccessContextDTO(is_participant=(user.team_id == team_id)),
                error_msg="Недостаточно прав для просмотра этой команды",
            )

            team = await self.uow.teams.get_team_by_id(team_id=team_id)

        if team is None:
            logger.info(f"Команда ID {team_id} не найдена.")
            raise TeamDoesNotExistsError("Команда не найдена")

        logger.success(
            f"Успешно получены данные команды ID: {team.id}, Название: {team.name}."
        )
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
        # Проверяем существование команды, чтобы избежать дубликатов
        async with self.uow:
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.TEAMS,
                action=Action.CREATE,
                error_msg="Недостаточно прав для создания команды",
            )

            is_exists = await self.uow.teams.check_team_name_exists(
                team_name=team_in.name
            )

            if is_exists:
                logger.info(f"Команда с названием {team_in.name} уже существует.")
                raise TeamAlreadyExistsError("Команда с таким названием уже существует")

            # Запускаем генерацию инвайт-кода в цикле, чтобы он был уникальным.
            # Если совпадений в Бд не найдено, то цикл завершается
            while True:
                code = self.generate_invite_code()
                is_code_exists = await self.uow.teams.check_invite_code_exists(
                    code=code
                )

                if not is_code_exists:
                    logger.info(
                        f"Инвайт код для команды {team_in.name} успешно сгенерирован."
                    )
                    break

            created_team = await self.uow.teams.create_team(
                team_in=team_in, invite_code=code
            )

            await self.uow.commit()

        logger.success(f"Команда {created_team.name} успешно создана.")
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
        if user.team_id is not None:
            logger.info(
                f"Пользователь ID: {user.id}, Email: {user.email} уже состоит в команде ID: {user.team_id}."
            )
            raise UserAlreadyInTeamError("Вы уже состоите в команде")

        async with self.uow:
            team = await self.uow.teams.get_team_by_invite_code(code=invite_code)

            if not team:
                logger.info(f"Инвайт код {invite_code} не найден.")
                raise TeamDoesNotExistsError("Команда с таким кодом не найдена")

            await self.uow.teams.add_user_to_team(user_id=user.id, team_id=team.id)
            await self.uow.commit()

        logger.success(f"Пользователь ID: {user.id} добавлен в команду ID: {team.id}")
        return team
