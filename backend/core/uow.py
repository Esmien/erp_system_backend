from abc import ABC, abstractmethod
from types import TracebackType

from backend.core.database.engine import async_session_maker
from backend.user.repository import UserRepository, AuthRepository, RegisterRepository
from backend.team.repository import TeamRepository
from backend.task.repository import TaskRepository
from backend.rbac.repository import RbacRepository


class IUnitOfWork(ABC):
    """Абстрактный интерфейс для Unit of Work"""

    users: UserRepository
    auth: AuthRepository
    register: RegisterRepository
    teams: TeamRepository
    tasks: TaskRepository
    rbac: RbacRepository

    @abstractmethod
    def __init__(self): ...

    @abstractmethod
    async def __aenter__(self): ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    @abstractmethod
    async def commit(self): ...

    @abstractmethod
    async def rollback(self): ...


class UnitOfWork(IUnitOfWork):
    """Конкретная реализация UoW для SQLAlchemy"""

    def __init__(self):
        self.session_factory = async_session_maker

    async def __aenter__(self):
        self.session = self.session_factory()

        self.users = UserRepository(self.session)
        self.auth = AuthRepository(self.session)
        self.register = RegisterRepository(self.session)
        self.teams = TeamRepository(self.session)
        self.tasks = TaskRepository(self.session)
        self.rbac = RbacRepository(self.session)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if exc_type:
            await self.rollback()

        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
