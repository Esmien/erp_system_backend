from backend.api.dependencies.permissions import get_current_user
from backend.api.main import app
from backend.api.tests.test_tasks_api.get_user_override import override_get_regular_user
from backend.core.constants import TaskStatus


async def test_get_task_by_id(client, open_task_json):
    create_response = await client.post("/api/v1/tasks/", json=open_task_json)
    create_response_json = create_response.json()

    task_id = create_response_json.get("id")

    response = await client.get(f"/api/v1/tasks/{task_id}/")
    response_json = response.json()

    assert response.status_code == 200
    assert response_json.get("title") == open_task_json["title"]


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


async def test_get_all_tasks_forbidden(client):
    old_dep = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = override_get_regular_user

    try:
        response = await client.get("/api/v1/tasks/?scope=all")
        assert response.status_code == 403
        assert response.json()["detail"] == "Недостаточно прав для просмотра всех задач"
    finally:
        # Возвращаем зависимость на место
        if old_dep:
            app.dependency_overrides[get_current_user] = old_dep
        else:
            app.dependency_overrides.pop(get_current_user, None)
