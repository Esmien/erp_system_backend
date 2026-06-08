from backend.api.dependencies.permissions import get_current_user
from backend.api.main import app
from tests.fixtures.environment_setup import (
    override_get_regular_user,
)


async def test_delete_task_success(client, open_task_json):
    create_response = await client.post("/api/v1/tasks/", json=open_task_json)
    task_id = create_response.json().get("id")

    response = await client.delete(f"/api/v1/tasks/{task_id}/")
    assert response.status_code == 204

    # Проверяем, что задача действительно исчезла
    get_response = await client.get(f"/api/v1/tasks/{task_id}/")
    assert get_response.status_code == 404


async def test_delete_foreign_task_forbidden(client, open_task_json):
    create_response = await client.post("/api/v1/tasks/", json=open_task_json)
    task_id = create_response.json().get("id")

    app.dependency_overrides[get_current_user] = override_get_regular_user

    response = await client.delete(f"/api/v1/tasks/{task_id}/")

    assert response.status_code == 403
    assert "недостаточно прав" in response.json()["detail"].lower()
