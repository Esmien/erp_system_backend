from backend.api.dependencies.permissions import get_current_user
from backend.api.main import app
from backend.api.tests.test_meeting_api.utils import get_future_times
from tests.fixtures.environment_setup import override_get_regular_user


async def test_get_all_meetings(client):
    start, end = get_future_times()
    await client.post(
        "/api/v1/meetings/",
        json={
            "theme": "Встреча для списка",
            "datetime_start": start,
            "datetime_end": end,
            "participant_ids": [],
        },
    )

    response = await client.get("/api/v1/meetings/")

    assert response.status_code == 200
    data = response.json()
    items = data.get("items", [])  # Извлекаем список
    assert len(items) >= 1
    assert any(m["theme"] == "Встреча для списка" for m in items)


async def test_get_meeting_by_id_success(client):
    start, end = get_future_times()
    create_resp = await client.post(
        "/api/v1/meetings/",
        json={
            "theme": "Детали встречи",
            "datetime_start": start,
            "datetime_end": end,
            "participant_ids": [],
        },
    )
    meeting_id = create_resp.json().get("id")

    response = await client.get(f"/api/v1/meetings/{meeting_id}/")

    assert response.status_code == 200
    assert response.json().get("theme") == "Детали встречи"


async def test_get_meeting_not_found(client):
    response = await client.get("/api/v1/meetings/99999/")
    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"].lower()


async def test_get_meeting_forbidden(client):
    start, end = get_future_times()
    create_resp = await client.post(
        "/api/v1/meetings/",
        json={
            "theme": "Секретная встреча",
            "datetime_start": start,
            "datetime_end": end,
            "participant_ids": [],
        },
    )
    meeting_id = create_resp.json().get("id")

    old_dep = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = override_get_regular_user

    try:
        response = await client.get(f"/api/v1/meetings/{meeting_id}/")
        assert response.status_code == 403
        assert (
            "вы не можете получить данные этой встречи"
            in response.json()["detail"].lower()
        )
    finally:
        if old_dep:
            app.dependency_overrides[get_current_user] = old_dep
        else:
            app.dependency_overrides.pop(get_current_user, None)
