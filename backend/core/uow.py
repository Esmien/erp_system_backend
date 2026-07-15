from abc import ABC, abstractmethod
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from backend.comment.repository import CommentRepository
from backend.core.database.engine import async_session_maker
from backend.evaluation.repository import EvaluationRepository
from backend.meeting.repository import MeetingRepository
from backend.rbac.repository import RbacRepository
from backend.task.repository import TaskRepository
from backend.team.repository import TeamRepository
from backend.user.repository import AuthRepository, RegisterRepository, UserRepository


class IUnitOfWork(ABC):
    """Абстрактный интерфейс для Unit of Work"""

    session: AsyncSession
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

    def __init__(self, session: AsyncSession | None = None):
        self.session = session if session is not None else async_session_maker()
        self.users = UserRepository(session=self.session)
        self.auth = AuthRepository(session=self.session)
        self.register = RegisterRepository(session=self.session)
        self.teams = TeamRepository(session=self.session)
        self.tasks = TaskRepository(session=self.session)
        self.comments = CommentRepository(session=self.session)
        self.rbac = RbacRepository(session=self.session)
        self.evaluations = EvaluationRepository(session=self.session)
        self.meetings = MeetingRepository(session=self.session)

    async def __aenter__(self):
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
