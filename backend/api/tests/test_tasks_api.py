from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.api.dependencies.permissions import get_current_user
from backend.api.main import app
from backend.core.constants import TaskStatus
from backend.user.models import User
from backend.user.schemas import UserDTO
from tests.fixtures.environment_setup import fixture_async_session_maker


async def override_get_regular_user():
    """Вспомогательная функция для переключения на обычного пользователя без прав"""
    async with fixture_async_session_maker() as session:
        stmt = (
            select(User)
            .where(User.email == "user@user.com")
            .options(selectinload(User.role))
        )
        result = await session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return UserDTO.model_validate(user_model) if user_model else None


async def test_create_task_success(client, task_in):
    response = await client.post("/api/v1/tasks/", json=task_in)

    data = response.json()

    assert response.status_code == 201
    assert data.get("title") == task_in["title"]
    assert "id" in data
    assert data.get("author_id") == 1


async def test_get_task_by_id(client, task_in):
    create_response = await client.post("/api/v1/tasks/", json=task_in)
    create_response_json = create_response.json()

    task_id = create_response_json.get("id")

    response = await client.get(f"/api/v1/tasks/{task_id}/")
    response_json = response.json()

    assert response.status_code == 200
    assert response_json.get("title") == task_in["title"]


async def test_get_task_not_found(client):
    response = await client.get("/api/v1/tasks/99999/")
    response_json = response.json()

    assert response.status_code == 404
    assert response_json == {"detail": "Задача не найдена."}


async def test_get_tasks_by_filters(client):
    task_1 = {"title": "Задача 1", "status": TaskStatus.OPEN}
    task_2 = {"title": "Задача 2", "status": TaskStatus.DONE}

    await client.post("/api/v1/tasks/", json=task_1)
    await client.post("/api/v1/tasks/", json=task_2)

    response_done = await client.get(
        f"/api/v1/tasks/?scope=all&task_status={TaskStatus.DONE}"
    )
    assert response_done.status_code == 200

    data = response_done.json()
    assert len(data) == 1
    assert data[0]["title"] == "Задача 2"


async def test_change_task_status(client, task_in):
    create_response = await client.post("/api/v1/tasks/", json=task_in)
    create_response_json = create_response.json()

    task_id = create_response_json.get("id")

    patch_data = {"status": TaskStatus.DONE}
    response = await client.patch(f"/api/v1/tasks/{task_id}/status/", json=patch_data)

    assert response.status_code == 200
    assert response.json().get("status") == TaskStatus.DONE


async def test_get_all_tasks_forbidden(client):
    old_dep = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = override_get_regular_user

    response = await client.get("/api/v1/tasks/?scope=all")

    if old_dep:
        app.dependency_overrides[get_current_user] = old_dep

    assert response.status_code == 403
    assert response.json()["detail"] == "Недостаточно прав для просмотра всех задач"


async def test_update_foreign_task_forbidden(client, task_in):
    create_response = await client.post("/api/v1/tasks/", json=task_in)
    task_id = create_response.json().get("id")

    old_dep = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = override_get_regular_user

    patch_data = {"status": TaskStatus.DONE}
    response = await client.patch(f"/api/v1/tasks/{task_id}/status/", json=patch_data)

    if old_dep:
        app.dependency_overrides[get_current_user] = old_dep

    assert response.status_code == 403
    assert response.json()["detail"] == "Недостаточно прав для изменения статуса"
