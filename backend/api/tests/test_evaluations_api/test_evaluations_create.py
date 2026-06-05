from backend.api.main import app
from backend.api.dependencies.permissions import get_current_user
from tests.fixtures.environment_setup import override_get_regular_user


async def test_evaluate_task_success(client, closed_task_id, evaluation_data):
    response = await client.post(
        f"/api/v1/tasks/{closed_task_id}/evaluation/", json=evaluation_data
    )
    data = response.json()

    assert response.status_code == 201
    assert data.get("value") == evaluation_data["value"]
    assert data.get("comment") == evaluation_data["comment"]
    assert data.get("task_id") == closed_task_id
    assert "id" in data


async def test_evaluate_task_not_completed(client, open_task_id, evaluation_data):
    response = await client.post(
        f"/api/v1/tasks/{open_task_id}/evaluation/", json=evaluation_data
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Задача еще не выполнена"


async def test_evaluate_task_already_evaluated(client, closed_task_id, evaluation_data):
    # Сначала ставим оценку
    await client.post(
        f"/api/v1/tasks/{closed_task_id}/evaluation/", json=evaluation_data
    )

    # Пытаемся поставить вторую оценку на ту же задачу
    response = await client.post(
        f"/api/v1/tasks/{closed_task_id}/evaluation/", json=evaluation_data
    )

    assert response.status_code == 400
    assert "уже оценена" in response.json()["detail"].lower()


async def test_evaluate_task_forbidden(client, closed_task_id, evaluation_data):
    # Переключаемся на обычного пользователя (у которого нет прав на CREATE оценок)
    old_dep = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = override_get_regular_user

    try:
        response = await client.post(
            f"/api/v1/tasks/{closed_task_id}/evaluation/", json=evaluation_data
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Недостаточно прав для оценки задачи"
    finally:
        # Возвращаем зависимость на место
        if old_dep:
            app.dependency_overrides[get_current_user] = old_dep
        else:
            app.dependency_overrides.pop(get_current_user, None)
