from backend.api.dependencies.permissions import get_current_user
from backend.api.tests.test_meeting_api.utils import get_future_times
from tests.fixtures.environment_setup import (
    override_get_regular_user,
)


async def test_delete_meeting_success(client):
    start, end = get_future_times()
    create_resp = await client.post(
        "/api/v1/meetings/",
        json={
            "theme": "На удаление",
            "datetime_start": start,
            "datetime_end": end,
            "participant_ids": [],
        },
    )
    meeting_id = create_resp.json().get("id")

    response = await client.delete(f"/api/v1/meetings/{meeting_id}/")
    assert response.status_code == 204

    # Проверяем, что она пропала
    get_response = await client.get(f"/api/v1/meetings/{meeting_id}/")
    assert get_response.status_code == 404


async def test_delete_meeting_not_found(client):
    response = await client.delete("/api/v1/meetings/99999/")
    assert response.status_code == 404


async def test_delete_foreign_meeting_forbidden(client, app):
    start, end = get_future_times()
    create_resp = await client.post(
        "/api/v1/meetings/",
        json={
            "theme": "Важная встреча",
            "datetime_start": start,
            "datetime_end": end,
            "participant_ids": [3],
        },
    )
    meeting_id = create_resp.json().get("id")

    app.dependency_overrides[get_current_user] = override_get_regular_user

    response = await client.delete(f"/api/v1/meetings/{meeting_id}/")

    assert response.status_code == 403
    assert "недостаточно прав" in response.json()["detail"].lower()
