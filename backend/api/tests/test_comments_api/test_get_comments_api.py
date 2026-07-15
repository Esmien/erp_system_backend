import pytest

from backend.rbac.api.permissions_dependencies import get_current_user
from tests.fixtures.environment_setup import override_get_regular_user


@pytest.mark.parametrize("count", [0, 10])
async def test_get_comments_success(client, count):
    comments = [{"text": f"Это {i} важный комментарий к задаче"} for i in range(1, count + 1)]
    for comment in comments:
        await client.post("/api/v1/tasks/1/comments/", json=comment)

    response = await client.get(url="/api/v1/tasks/1/comments/")
    response_json = response.json()
    items = response_json.get("items", [])  # Извлекаем список из пагинации

    if comments:
        second_comment = items[1].get("text")
        assert second_comment == "Это 2 важный комментарий к задаче"

    assert response.status_code == 200
    assert len(items) == count
    assert response_json.get("total") == count  # Заодно проверяем total


async def test_get_comments_of_not_exists_task(client):
    response = await client.get(url="/api/v1/tasks/9999/comments/")

    assert response.json().get("detail") == "Задача не найдена."
    assert response.status_code == 404


async def test_get_comments_forbidden(client, app):
    app.dependency_overrides[get_current_user] = override_get_regular_user

    await client.post("/api/v1/tasks/1/comments/", json={"text": "Комментарий к чужой задаче"})
    response = await client.get(url="/api/v1/tasks/1/comments/")
    assert response.status_code == 403
    assert response.json().get("detail") == "Вы не являетесь участником задачи, комментарии недоступны."
