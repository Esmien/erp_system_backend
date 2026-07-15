from unittest.mock import AsyncMock

import pytest

from backend.core.enums import TaskStatus
from backend.evaluation.repository import EvaluationRepository
from backend.evaluation.service import EvaluationService
from backend.task.models import Task
from backend.user.models import User
from backend.user.schemas import UserDTO


@pytest.fixture
def eval_repo(db_session):
    return EvaluationRepository(session=db_session)


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


@pytest.fixture
def evaluation_data():
    return {"value": 5, "comment": "Отличная работа, все в срок!"}


@pytest.fixture
async def closed_task_id(client, closed_task_json) -> int:
    """Создает завершенную задачу через API и возвращает её ID"""
    response = await client.post("/api/v1/tasks/", json=closed_task_json)
    assert response.status_code == 201, "Не удалось создать closed_task для теста"
    return response.json()["id"]


@pytest.fixture
async def open_task_id(client, open_task_json) -> int:
    """Создает открытую задачу через API и возвращает её ID"""
    response = await client.post("/api/v1/tasks/", json=open_task_json)
    assert response.status_code == 201, "Не удалось создать open_task для теста"
    return response.json()["id"]
