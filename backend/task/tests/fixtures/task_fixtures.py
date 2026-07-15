from datetime import UTC, datetime

import pytest

from backend.core.enums import RoleName, TaskStatus
from backend.task.repository import TaskRepository
from backend.task.schemas import TaskCreate, TaskRead
from backend.task.service import TaskService
from backend.user.schemas import RoleDTO, UserDTO


@pytest.fixture
def task_repo(db_session):
    return TaskRepository(session=db_session)


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
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def task_in_json():
    return {
        "title": "Настроить CI/CD",
        "description": "Дописать Github Actions для деплоя",
        "expire": "2026-12-31",
    }


@pytest.fixture
def closed_task_json(task_in_json):
    return task_in_json | {"status": TaskStatus.DONE}


@pytest.fixture
def open_task_json(task_in_json):
    return task_in_json | {"status": TaskStatus.OPEN}
