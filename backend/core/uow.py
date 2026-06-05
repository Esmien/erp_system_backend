from abc import ABC, abstractmethod
from types import TracebackType

from backend.comment.repository import CommentRepository
from backend.core.database.engine import async_session_maker
from backend.evaluation.repository import EvaluationRepository
from backend.meeting.repository import MeetingRepository
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
    comments: CommentRepository
    rbac: RbacRepository
    evaluations: EvaluationRepository
    meetings: MeetingRepository

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
        self._session_cm = self.session_factory()
        self.session = await self._session_cm.__aenter__()

        self.users = UserRepository(session=self.session)
        self.auth = AuthRepository(session=self.session)
        self.register = RegisterRepository(session=self.session)
        self.teams = TeamRepository(session=self.session)
        self.tasks = TaskRepository(session=self.session)
        self.comments = CommentRepository(session=self.session)
        self.rbac = RbacRepository(session=self.session)
        self.evaluations = EvaluationRepository(session=self.session)
        self.meetings = MeetingRepository(session=self.session)

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
