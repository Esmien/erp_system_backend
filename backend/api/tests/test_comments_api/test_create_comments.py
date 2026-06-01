from backend.api.dependencies.permissions import get_current_user
from backend.api.main import app
from backend.api.tests.test_tasks_api.get_user_override import override_get_regular_user


async def test_add_comment_success(client):
    comment_data = {"text": "Это важный комментарий к задаче"}
    response = await client.post("/api/v1/tasks/1/comments/", json=comment_data)

    data = response.json()

    assert response.status_code == 201
    assert data.get("text") == comment_data["text"]
    assert data.get("task_id") == 1
    assert "id" in data


async def test_add_comment_task_not_found(client):
    comment_data = {"text": "Комментируем пустоту"}
    response = await client.post("/api/v1/tasks/9999/comments/", json=comment_data)

    assert response.status_code == 404
    assert response.json()["detail"] == "Задача не найдена."


async def test_add_comment_forbidden(client):
    # Переключаемся на обычного пользователя, который не является автором/исполнителем
    old_dep = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = override_get_regular_user

    try:
        comment_data = {"text": "Попытка прокомментировать чужую задачу"}
        response = await client.post("/api/v1/tasks/1/comments/", json=comment_data)
        assert response.status_code == 403
        assert "не ваша задача" in response.json()["detail"]
    finally:
        # Возвращаем зависимость на место
        if old_dep:
            app.dependency_overrides[get_current_user] = old_dep
        else:
            app.dependency_overrides.pop(get_current_user, None)
