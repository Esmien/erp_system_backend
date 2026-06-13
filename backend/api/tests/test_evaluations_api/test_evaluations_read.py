from backend.api.dependencies.permissions import get_current_user
from tests.fixtures.environment_setup import override_get_regular_user


async def test_get_evaluation_success(client, closed_task_id, evaluation_data):
    await client.post(
        f"/api/v1/tasks/{closed_task_id}/evaluation/", json=evaluation_data
    )

    response = await client.get(f"/api/v1/tasks/{closed_task_id}/evaluation/")
    data = response.json()

    assert response.status_code == 200
    assert data is not None
    assert data.get("value") == evaluation_data["value"]
    assert data.get("comment") == evaluation_data["comment"]
    assert data.get("task_id") == closed_task_id
    assert "id" in data


async def test_get_evaluation_empty(client):
    response = await client.get("/api/v1/tasks/1/evaluation/")

    assert response.status_code == 200
    assert response.json() is None


async def test_get_evaluation_task_not_found(client):
    response = await client.get("/api/v1/tasks/9999/evaluation/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Задача не найдена."


async def test_get_evaluation_forbidden(client, closed_task_id, evaluation_data, app):
    # Ставим оценку под админом
    await client.post(
        f"/api/v1/tasks/{closed_task_id}/evaluation/", json=evaluation_data
    )

    app.dependency_overrides[get_current_user] = override_get_regular_user

    # Пытаемся подсмотреть чужую оценку
    response = await client.get(f"/api/v1/tasks/{closed_task_id}/evaluation/")
    assert response.status_code == 403
    assert response.json()["detail"] == "У вас нет прав для просмотра этой оценки"
