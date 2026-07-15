from backend.meeting.tests.test_meeting_api.utils import get_future_times
from backend.rbac.api.permissions_dependencies import get_current_user
from tests.fixtures.environment_setup import (
    override_get_regular_user,
)


async def test_update_meeting_success(client):
    start, end = get_future_times()
    create_resp = await client.post(
        "/api/v1/meetings/",
        json={
            "theme": "Тема до обновления",
            "datetime_start": start,
            "datetime_end": end,
            "participant_ids": [2],
        },
    )
    meeting_id = create_resp.json().get("id")

    update_data = {"theme": "Обновленная тема", "participant_ids": [3]}
    response = await client.patch(f"/api/v1/meetings/{meeting_id}/", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data.get("theme") == "Обновленная тема"
    assert len(data.get("participants")) == 1
    assert data.get("participants")[0]["id"] == 3


async def test_update_meeting_not_found(client):
    update_data = {"theme": "Попытка обновить пустышку"}
    response = await client.patch("/api/v1/meetings/99999/", json=update_data)
    assert response.status_code == 404


async def test_update_foreign_meeting_forbidden(client, app):
    start, end = get_future_times()
    create_resp = await client.post(
        "/api/v1/meetings/",
        json={
            "theme": "Чужая встреча",
            "datetime_start": start,
            "datetime_end": end,
            "participant_ids": [3],
        },
    )
    meeting_id = create_resp.json().get("id")

    app.dependency_overrides[get_current_user] = override_get_regular_user

    update_data = {"theme": "Хак темы"}
    response = await client.patch(f"/api/v1/meetings/{meeting_id}/", json=update_data)
    assert response.status_code == 403
    assert "данные встречи может обновить только автор или руководитель" in response.json()["detail"].lower()
