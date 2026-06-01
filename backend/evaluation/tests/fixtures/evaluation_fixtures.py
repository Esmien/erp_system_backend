from unittest.mock import AsyncMock

import pytest

from backend.evaluation.repository import EvaluationRepository
from backend.evaluation.service import EvaluationService
from backend.user.models import User
from backend.task.models import Task
from backend.core.constants import TaskStatus
from backend.user.schemas import UserDTO


@pytest.fixture
def eval_repo(db_session):
    return EvaluationRepository(session=db_session)


@pytest.fixture
def mock_rbac_service():
    service = AsyncMock()
    service.enforce_permission.return_value = None
    service.check_permission.return_value = True
    return service


@pytest.fixture
def eval_service(mock_uow, mock_rbac_service):
    mock_rbac_service.check_permission = AsyncMock(return_value=True)
    return EvaluationService(uow=mock_uow, rbac_service=mock_rbac_service)


@pytest.fixture
def test_user():
    return UserDTO(
        id=1,
        name="Test",
        email="test@test.com",
        role_id=1,
        is_active=True,
        hashed_password="123",
    )


@pytest.fixture
async def test_user_db(db_session):
    """Создает тестового юзера в БД для FK"""
    user = User(email="repo@test.com", name="Test", hashed_password="123", role_id=1)
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def test_task_db(db_session, test_user_db):
    """Создает тестовую задачу в БД для FK"""
    task = Task(
        title="Test Repo Task",
        description="Desc",
        author_id=test_user_db.id,
        executor_id=test_user_db.id,
        status=TaskStatus.DONE,
    )
    db_session.add(task)
    await db_session.flush()
    return task
