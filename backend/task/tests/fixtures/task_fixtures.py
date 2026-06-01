from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from backend.core.constants import TaskStatus, RoleName
from backend.task.repository import TaskRepository
from backend.task.schemas import TaskCreate, TaskRead
from backend.task.service import TaskService
from backend.user.schemas import UserDTO, RoleDTO
from backend.rbac.service import RbacService


@pytest.fixture
def task_repo(db_session):
    return TaskRepository(session=db_session)


@pytest.fixture
def mock_rbac_service():
    """Мок для проверки динамических прав"""
    service = AsyncMock(spec=RbacService)
    # По умолчанию даем доступ во всех тестах
    service.check_permission.return_value = True
    return service


@pytest.fixture
def task_service(mock_uow, mock_rbac_service):
    return TaskService(uow=mock_uow, rbac_service=mock_rbac_service)


@pytest.fixture
def task_in():
    return TaskCreate(
        title="Тестовая задача",
        description="Описание тестовой задачи",
        status=TaskStatus.OPEN,
    )


@pytest.fixture
def mock_user_author():
    return UserDTO(
        id=1,
        email="author@test.com",
        hashed_password="hash",
        name="Author",
        role_id=3,
        role=RoleDTO(id=3, name=RoleName.USER),
        is_active=True,
    )


@pytest.fixture
def mock_user_stranger():
    return UserDTO(
        id=2,
        email="stranger@test.com",
        hashed_password="hash",
        name="Stranger",
        role_id=3,
        role=RoleDTO(id=3, name=RoleName.USER),
        is_active=True,
    )


@pytest.fixture
def sample_task():
    return TaskRead(
        id=1,
        title="Тест",
        description="Описание",
        status=TaskStatus.OPEN,
        author_id=1,
        executor_id=None,
        created_at=datetime.now(timezone.utc),
    )
